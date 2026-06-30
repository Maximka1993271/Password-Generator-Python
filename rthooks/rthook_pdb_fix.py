"""
PyInstaller runtime hook — restore clean stdlib pdb before any app code runs.

When pdbpp is installed in the build environment, PyInstaller bundles the
patched pdb.py (which loads pdbpp.py) but NOT pdbpp.py itself.
This hook removes every pdbpp-related module from sys.modules and blocks
future imports, so that construct/pykeepass can load the real pdb safely.
"""
import sys
import os

def _fix_pdb() -> None:
    # 1. Evict any already-loaded pdbpp / pdb stubs
    for key in list(sys.modules):
        if any(x in key.lower() for x in ("pdbpp", "fancycompleter", "pyrepl")):
            sys.modules.pop(key, None)

    # 2. Install empty-module blockers so future import attempts silently no-op
    class _BlockedModule:
        """Stub that satisfies import without doing anything."""
        __all__: list = []
        def __getattr__(self, name: str):
            return None
        def __bool__(self) -> bool:
            return False

    for name in ("pdbpp", "pdbpp_utils", "fancycompleter",
                 "pyrepl", "pyrepl.readline", "pyrepl.input"):
        if name not in sys.modules:
            stub = _BlockedModule()
            stub.__name__ = name          # type: ignore[attr-defined]
            sys.modules[name] = stub      # type: ignore[assignment]

    # 3. Try to reload a clean pdb from the frozen bundle
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        pdb_path = os.path.join(meipass, "pdb.py")
        if os.path.isfile(pdb_path):
            import importlib.util
            try:
                spec   = importlib.util.spec_from_file_location("pdb", pdb_path)
                module = importlib.util.module_from_spec(spec)      # type: ignore[arg-type]
                spec.loader.exec_module(module)                      # type: ignore[union-attr]
                sys.modules["pdb"] = module
            except Exception:
                pass  # non-fatal — let Python fall back naturally

_fix_pdb()
