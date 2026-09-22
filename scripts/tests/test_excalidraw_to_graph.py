"""python3 -m unittest discover scripts/tests   (stdlib only)"""

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("e2g", HERE.parent / "excalidraw_to_graph.py")
e2g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e2g)


class MiniScene(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = e2g.build(e2g.load_elements(HERE / "fixtures" / "mini.excalidraw"))
        cls.nodes = cls.graph["nodes"]
        cls.by_label = {n.label: n for n in cls.nodes.values() if n.label != "Click Receiver"}

    def edge(self, src, dst):
        for e in self.graph["edges"]:
            if e.src == src and e.dst == dst:
                return e
        self.fail(f"no edge {src} -> {dst}: {[(e.src, e.dst) for e in self.graph['edges']]}")

    def test_nodes_and_labels(self):
        self.assertEqual(len(self.nodes), 7)  # deleted element ignored
        self.assertEqual(self.nodes["gw"].label, "API Gateway")
        self.assertEqual(self.nodes["F"].label, "Ingest")
        self.assertEqual(self.nodes["pool"].label, "Click Receiver pool")
        self.assertTrue(self.nodes["pool"].label_inferred)
        self.assertEqual(self.nodes["db"].label, "DB")
        self.assertIn("Tables:\nClick(id, ad_id)", self.nodes["db"].details)

    def test_containment(self):
        self.assertEqual(self.nodes["r1"].parent, "pool")
        self.assertTrue(self.nodes["r1"].parent_inferred)
        self.assertEqual(self.nodes["pool"].parent, "F")
        self.assertFalse(self.nodes["pool"].parent_inferred)
        self.assertIsNone(self.nodes["db"].parent)

    def test_bound_edge_with_label(self):
        e = self.edge("gw", "r1")
        self.assertEqual(e.label, "POST /click")
        self.assertEqual(e.direction, "->")
        self.assertEqual(e.inferred, [])

    def test_unbound_end_snaps_to_nearby_shape(self):
        e = self.edge("r1", "kafka")
        self.assertEqual(e.inferred, ["target"])

    def test_bidirectional_and_triangle_heads(self):
        self.assertEqual(self.edge("db", "gw").direction, "<->")
        self.assertEqual(self.edge("kafka", "db").direction, "->")

    def test_decorative_line_skipped(self):
        self.assertEqual(len(self.graph["edges"]), 4)

    def test_notes_groups_warnings(self):
        notes = [n["text"] for n in self.graph["notes"]]
        self.assertEqual(notes, ["Requirements\n- low latency"])
        self.assertEqual(self.graph["groups"], [[self.nodes["kafka"].ref, self.nodes["r2"].ref]])
        self.assertTrue(any("proximity" in w for w in self.graph["warnings"]))

    def test_markdown_renders(self):
        md = e2g.render_markdown(self.graph, "mini.excalidraw")
        self.assertIn("API Gateway -> ", md)
        self.assertIn('"POST /click"', md)
        self.assertIn("(inferred target)", md)
        self.assertIn("## Notes", md)


if __name__ == "__main__":
    unittest.main()
