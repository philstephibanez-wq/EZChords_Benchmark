from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("nav_r3a3", ROOT/"scripts"/"migrate-nav-active-r3a3.py")
mod=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

samples = [
"""<!doctype html><html><head><style>.main-nav a{color:white}</style></head>
<body><nav class="main-nav"><a href="/#import">Import</a><a href="/#stems">Stems</a></nav></body></html>""",
"""<!doctype html>\r\n<html>\r\n<head>\r\n<style>\r\n.main-nav a{color:white}\r\n</style>\r\n</head>\r\n<body>\r\n<nav class="main-nav"></nav>\r\n</body>\r\n</html>\r\n""",
]
for sample in samples:
    out=mod.patch_text(sample)
    assert "EZSTUDIO_NAV_ACTIVE_R3A3_CSS" in out
    assert "EZSTUDIO_NAV_ACTIVE_R3A3_JS" in out
    assert '.main-nav a.active' in out
    assert "IntersectionObserver" in out
    assert mod.patch_text(out) == out

print("EZSTUDIO_NAV_ACTIVE_R3A3_SYNTHETIC_OK")
