"""
PyInstaller hook for the construct binary-parsing library.
Excludes construct.debug (which triggers the pdb → pdbpp chain).
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports   = [m for m in collect_submodules("construct") if "debug" not in m]
datas: list     = []
excludedimports = ["pdbpp", "pdbpp_utils", "fancycompleter", "pyrepl", "construct.debug"]
