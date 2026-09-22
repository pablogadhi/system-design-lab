#!/usr/bin/env python3
"""Turn an Excalidraw scene (.excalidraw JSON) into a compact graph an agent can reason about.

    python3 scripts/excalidraw_to_graph.py design/diagram.excalidraw -o design/diagram.graph.md
    python3 scripts/excalidraw_to_graph.py design/diagram.excalidraw --json

Output sections:
  Components   shapes with their label (+ extra text inside them) and parent container
  Connections  arrows as `A -> B : label`, resolved through arrow bindings
  Groups       shapes grouped together in Excalidraw
  Notes        free text (requirements, tables, data flow...) grouped by frame
  Warnings     everything that was guessed — ask the user about these

Anything derived from geometry instead of explicit bindings is marked `(inferred)`.
Read it together with diagram.png: the image carries layout and visual meaning, this carries wiring.
Stdlib only.
"""

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

SHAPES = {"rectangle", "ellipse", "diamond", "frame", "magicframe", "image", "embeddable", "iframe"}
CONNECTORS = {"arrow", "line"}
SNAP_DISTANCE = 40.0  # px: an unbound arrow end this close to a shape is assumed to connect to it


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @classmethod
    def of(cls, el: dict) -> "Box":
        x, y, w, h = el.get("x", 0), el.get("y", 0), el.get("width", 0), el.get("height", 0)
        # negative width/height happen when shapes are drawn right-to-left
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        return cls(x, y, w, h)

    @property
    def area(self) -> float:
        return self.w * self.h

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    def contains_point(self, p: tuple[float, float]) -> bool:
        return self.x <= p[0] <= self.x + self.w and self.y <= p[1] <= self.y + self.h

    def contains(self, other: "Box") -> bool:
        return (
            self.x <= other.x
            and self.y <= other.y
            and other.x + other.w <= self.x + self.w
            and other.y + other.h <= self.y + self.h
            and self.area > other.area
        )

    def distance(self, p: tuple[float, float]) -> float:
        dx = max(self.x - p[0], 0, p[0] - (self.x + self.w))
        dy = max(self.y - p[1], 0, p[1] - (self.y + self.h))
        return math.hypot(dx, dy)


@dataclass
class Node:
    id: str
    ref: str  # short stable id for the output: n1, n2...
    kind: str
    box: Box
    label: str = ""
    label_inferred: bool = False
    details: list[str] = field(default_factory=list)
    parent: str | None = None
    parent_inferred: bool = False
    frame: str | None = None


@dataclass
class Edge:
    src: str | None
    dst: str | None
    label: str
    direction: str  # "->", "<-", "<->", "--"
    inferred: list[str]
    arrow_id: str


def clean(text: str) -> str:
    return " ".join((text or "").split())


def load_elements(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if data.get("type") not in (None, "excalidraw"):
        raise SystemExit(f"{path}: not an Excalidraw scene (type={data.get('type')})")
    return [e for e in data.get("elements", []) if not e.get("isDeleted")]


def build(elements: list[dict]) -> dict:
    by_id = {e["id"]: e for e in elements}
    warnings: list[str] = []

    # -- nodes -----------------------------------------------------------------------------
    shape_els = sorted(
        (e for e in elements if e["type"] in SHAPES), key=lambda e: (Box.of(e).y, Box.of(e).x)
    )
    nodes: dict[str, Node] = {}
    for i, e in enumerate(shape_els, 1):
        nodes[e["id"]] = Node(id=e["id"], ref=f"n{i}", kind=e["type"], box=Box.of(e), frame=e.get("frameId"))
        if e["type"] in ("frame", "magicframe") and e.get("name"):
            nodes[e["id"]].label = clean(e["name"])

    texts = [e for e in elements if e["type"] == "text"]
    arrow_labels: dict[str, str] = {}
    free_texts: list[dict] = []
    for t in texts:
        container = t.get("containerId")
        content = clean(t.get("originalText") or t.get("text"))
        if not content:
            continue
        if container in nodes:
            node = nodes[container]
            node.label = f"{node.label} / {content}" if node.label else content
        elif container and by_id.get(container, {}).get("type") in CONNECTORS:
            arrow_labels[container] = content
        else:
            free_texts.append(t)

    def smallest_shape_containing(point: tuple[float, float], exclude: str | None = None) -> Node | None:
        candidates = [
            n for n in nodes.values()
            if n.id != exclude and n.kind not in ("frame", "magicframe") and n.box.contains_point(point)
        ]
        return min(candidates, key=lambda n: n.box.area) if candidates else None

    # free text sitting inside a shape: label it (if unlabeled) or attach as details
    notes: list[dict] = []
    for t in sorted(free_texts, key=lambda t: (t.get("y", 0), t.get("x", 0))):
        content = t.get("originalText") or t.get("text") or ""
        host = smallest_shape_containing(Box.of(t).center)
        if host is None:
            notes.append(t)
        elif not host.label and "\n" not in content.strip():
            host.label, host.label_inferred = clean(content), True
        else:
            host.details.append(content.strip())

    # -- containment -----------------------------------------------------------------------
    group_members: dict[str, list[str]] = {}
    for e in shape_els:
        for g in e.get("groupIds") or []:
            group_members.setdefault(g, []).append(e["id"])

    # nearest enclosing shape first (e.g. "Click Receiver" inside "Click Receiver pool"), else its frame
    for n in nodes.values():
        containers = [
            o for o in nodes.values()
            if o.id != n.id and o.kind not in ("frame", "magicframe") and o.box.contains(n.box)
        ]
        if containers:
            n.parent = min(containers, key=lambda o: o.box.area).id
            n.parent_inferred = True
        elif n.frame and n.frame in nodes:
            n.parent = n.frame

    # -- edges -----------------------------------------------------------------------------
    edges: list[Edge] = []

    def resolve_end(binding: dict | None, point: tuple[float, float], exclude: str) -> tuple[str | None, bool]:
        """Returns (node id, inferred?)."""
        if binding and binding.get("elementId"):
            target = binding["elementId"]
            if target in nodes:
                return target, False
            el = by_id.get(target)
            if el and el.get("containerId") in nodes:  # bound to a text inside a shape
                return el["containerId"], False
            if el and el["type"] == "text":  # bound to free text: use the shape under it, if any
                host = smallest_shape_containing(Box.of(el).center)
                if host:
                    return host.id, True
        candidates = [
            (n.box.distance(point), n.box.area, n.id)
            for n in nodes.values()
            if n.id != exclude and n.kind not in ("frame", "magicframe")
        ]
        candidates = [c for c in candidates if c[0] <= SNAP_DISTANCE]
        if not candidates:
            return None, True
        return min(candidates)[2], True

    for e in elements:
        if e["type"] not in CONNECTORS:
            continue
        pts = e.get("points") or [[0, 0], [0, 0]]
        start = (e["x"] + pts[0][0], e["y"] + pts[0][1])
        end = (e["x"] + pts[-1][0], e["y"] + pts[-1][1])
        src, src_inf = resolve_end(e.get("startBinding"), start, exclude="")
        dst, dst_inf = resolve_end(e.get("endBinding"), end, exclude=src or "")
        if e["type"] == "line" and not (e.get("startBinding") or e.get("endBinding")) and not arrow_labels.get(e["id"]):
            continue  # decorative line
        head_s, head_e = e.get("startArrowhead"), e.get("endArrowhead")
        if e["type"] == "arrow" and head_e is None and head_s is None:
            head_e = "arrow"  # plain arrows default to an end arrowhead in older scenes
        direction = {(False, True): "->", (True, False): "<-", (True, True): "<->"}.get(
            (bool(head_s), bool(head_e)), "--"
        )
        inferred = [side for side, flag in (("source", src_inf), ("target", dst_inf)) if flag]
        edges.append(Edge(src, dst, arrow_labels.get(e["id"], ""), direction, inferred, e["id"]))
        if src is None or dst is None:
            where = "start" if src is None else "end"
            warnings.append(
                f"arrow {e['id'][:8]} ({arrow_labels.get(e['id'], 'no label')}): {where} not attached to any shape"
            )

    unlabeled = [n for n in nodes.values() if not n.label and n.kind not in ("frame", "magicframe")]
    for n in unlabeled:
        if any(e.src == n.id or e.dst == n.id for e in edges):
            warnings.append(f"{n.ref} ({n.kind}) has connections but no label")
    inferred_edges = sum(1 for e in edges if e.inferred)
    if inferred_edges:
        warnings.append(
            f"{inferred_edges} connection(s) resolved by proximity (arrows not snapped to shapes) — verify them"
        )

    groups = [
        sorted((nodes[m].ref for m in members), key=lambda r: int(r[1:]))
        for members in group_members.values()
        if len(members) > 1
    ]
    return {"nodes": nodes, "edges": edges, "groups": groups, "notes": notes, "warnings": warnings}


def name_of(nodes: dict[str, Node], node_id: str | None) -> str:
    if node_id is None:
        return "?"
    n = nodes[node_id]
    return f"{n.ref} {n.label or '(' + n.kind + ')'}"


def render_markdown(graph: dict, source: str) -> str:
    nodes: dict[str, Node] = graph["nodes"]
    out = [
        f"# Diagram graph: {source}",
        "",
        "_Generated by `scripts/excalidraw_to_graph.py`. Read together with `diagram.png`. "
        "`(inferred)` = derived from geometry, not explicit bindings._",
        "",
        f"## Components ({len(nodes)})",
    ]
    for n in sorted(nodes.values(), key=lambda n: int(n.ref[1:])):
        line = f"- **{n.ref}** {n.label or '(unlabeled)'} — {n.kind}"
        if n.label_inferred:
            line += " (label inferred)"
        if n.parent:
            line += f"; inside {name_of(nodes, n.parent)}" + (" (inferred)" if n.parent_inferred else "")
        out.append(line)
        for d in n.details:
            out.append("  - " + d.replace("\n", "\n    "))

    out += ["", f"## Connections ({len(graph['edges'])})"]
    for e in graph["edges"]:
        line = f"- {name_of(nodes, e.src)} {e.direction} {name_of(nodes, e.dst)}"
        if e.label:
            line += f' : "{e.label}"'
        if e.inferred:
            line += f" (inferred {', '.join(e.inferred)})"
        out.append(line)

    if graph["groups"]:
        out += ["", "## Groups"]
        out += [f"- {', '.join(g)}" for g in graph["groups"]]

    if graph["notes"]:
        out += ["", "## Notes (free text, top-to-bottom)"]
        for t in graph["notes"]:
            frame = t.get("frameId")
            prefix = f"[{name_of(nodes, frame)}] " if frame in nodes else ""
            body = (t.get("originalText") or t.get("text") or "").strip()
            out.append("")
            out.append(prefix + body.replace("\n", "  \n"))

    out += ["", "## Warnings"]
    out += [f"- {w}" for w in graph["warnings"]] or ["- none"]
    return "\n".join(out) + "\n"


def render_json(graph: dict) -> str:
    nodes: dict[str, Node] = graph["nodes"]
    ref = lambda i: nodes[i].ref if i in nodes else None  # noqa: E731
    return json.dumps(
        {
            "components": [
                {
                    "ref": n.ref, "label": n.label, "kind": n.kind, "details": n.details,
                    "parent": ref(n.parent), "parent_inferred": n.parent_inferred,
                }
                for n in nodes.values()
            ],
            "connections": [
                {"from": ref(e.src), "to": ref(e.dst), "direction": e.direction, "label": e.label,
                 "inferred": e.inferred}
                for e in graph["edges"]
            ],
            "groups": graph["groups"],
            "notes": [(t.get("originalText") or t.get("text") or "").strip() for t in graph["notes"]],
            "warnings": graph["warnings"],
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("scene", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    graph = build(load_elements(args.scene))
    text = render_json(graph) if args.json else render_markdown(graph, args.scene.name)
    if args.output:
        args.output.write_text(text)
        print(f"wrote {args.output} ({len(graph['nodes'])} components, {len(graph['edges'])} connections, "
              f"{len(graph['warnings'])} warnings)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
