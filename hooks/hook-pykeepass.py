"""
PyInstaller hook for pykeepass — collects all submodules but
excludes construct.debug to avoid the pdbpp chain.
"""
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    collect_submodules("pykeepass") +
    ["lxml", "lxml.etree", "cryptography",
     "construct.lib", "construct.core", "construct.expr"]
)
datas           = collect_data_files("pykeepass")
excludedimports = ["pdbpp", "pdbpp_utils", "construct.debug"]
