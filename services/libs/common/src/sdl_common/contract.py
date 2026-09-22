"""Check a FastAPI app against its contract in design/contracts/openapi/<service>.yaml.

Used by each service's tests so the services-builder and client-builder agents (who both work
from the contract) cannot silently drift apart:

    def test_matches_contract():
        assert_implements_contract(app, "sample-api")
"""

from pathlib import Path

import yaml
from fastapi import FastAPI

METHODS = {"get", "post", "put", "patch", "delete"}


def find_repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / "stack.yaml").exists() and (parent / "design").is_dir():
            return parent
    raise FileNotFoundError("repo root (with stack.yaml) not found")


def contract_path(service: str) -> Path:
    return find_repo_root(Path.cwd()) / "design" / "contracts" / "openapi" / f"{service}.yaml"


def operations(spec: dict) -> dict[tuple[str, str], set[str]]:
    ops = {}
    for path, item in (spec.get("paths") or {}).items():
        for method, op in item.items():
            if method in METHODS:
                ops[(method.upper(), path)] = set((op or {}).get("responses", {}).keys())
    return ops


def missing_operations(app: FastAPI, service: str) -> list[str]:
    contract = yaml.safe_load(contract_path(service).read_text())
    implemented = operations(app.openapi())
    problems = []
    for (method, path), statuses in operations(contract).items():
        if (method, path) not in implemented:
            problems.append(f"{method} {path}: not implemented")
            continue
        documented = implemented[(method, path)]
        for status in statuses:
            # FastAPI documents success codes + 422 automatically; explicit error codes need `responses=`
            if status not in documented and not status.startswith("2"):
                problems.append(f"{method} {path}: response {status} not declared (add responses={{...}})")
    return problems


def assert_implements_contract(app: FastAPI, service: str) -> None:
    problems = missing_operations(app, service)
    assert not problems, "contract drift for " + service + ":\n  " + "\n  ".join(problems)
