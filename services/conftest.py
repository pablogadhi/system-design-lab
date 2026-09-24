"""Workspace-wide pytest setup.

pytest's importlib mode names a test file after its folders (services/zeta/tests/test_app.py ->
"zeta.tests.test_app") and builds any missing parent package from those folders. When a service's
folder has the same name as its module (single-word services like `zeta`), that stand-in package
would shadow the real one and `from zeta.main import app` fails. Importing every service package up
front makes pytest reuse the real module instead.
"""

import importlib
from pathlib import Path

ROOT = Path(__file__).parent

for init in sorted(ROOT.glob("*/src/*/__init__.py")):
    if init.relative_to(ROOT).parts[0] != "_template":
        importlib.import_module(init.parent.name)
