from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "templates" / "base.html.twig"

CSS_MARKER = "EZSTUDIO_NAV_ACTIVE_R3A3_CSS"
JS_MARKER = "EZSTUDIO_NAV_ACTIVE_R3A3_JS"

CSS = r"""
/* EZSTUDIO_NAV_ACTIVE_R3A3_CSS */
.main-nav a.active,
.main-nav a[aria-current="page"]{
  background:#f5f6f8;
  color:#17191d;
  border-color:#f5f6f8;
  font-weight:700;
  box-shadow:0 0 0 1px rgba(255,255,255,.12) inset;
}
.main-nav a.active:hover,
.main-nav a[aria-current="page"]:hover{
  background:#fff;
}
"""

JS = r"""
<script>
/* EZSTUDIO_NAV_ACTIVE_R3A3_JS */
(() => {
  const nav = document.querySelector('.main-nav');
  if (!nav) return;

  const links = Array.from(nav.querySelectorAll('a[href]'));
  const bySection = new Map();

  for (const link of links) {
    const href = link.getAttribute('href') || '';
    const hashIndex = href.indexOf('#');
    if (hashIndex >= 0) {
      const section = href.slice(hashIndex + 1).trim().toLowerCase();
      if (section) bySection.set(section, link);
    }
  }

  const setActive = (section) => {
    const wanted = (section || '').toLowerCase();
    for (const link of links) {
      const active = bySection.get(wanted) === link;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
  };

  const sectionFromLocation = () => {
    const hash = (window.location.hash || '').replace(/^#/, '').toLowerCase();
    if (bySection.has(hash)) return hash;

    const path = window.location.pathname.toLowerCase();
    if (path.includes('/stems')) return 'stems';
    if (path.includes('/lyrics')) return 'lyrics';
    if (path.includes('/chords')) return 'chords';

    return 'import';
  };

  setActive(sectionFromLocation());

  window.addEventListener('hashchange', () => {
    setActive(sectionFromLocation());
  });

  for (const [section, link] of bySection.entries()) {
    link.addEventListener('click', () => setActive(section));
  }

  const observed = ['import','stems','chords','lyrics','runs']
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if ('IntersectionObserver' in window && observed.length) {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a,b) => b.intersectionRatio - a.intersectionRatio);
      if (visible.length) setActive(visible[0].target.id);
    }, {
      rootMargin:'-20% 0px -55% 0px',
      threshold:[0.05,0.2,0.5]
    });
    observed.forEach((node) => observer.observe(node));
  }
})();
</script>
"""

def inject_once(text: str, marker: str, payload: str, closing_tag: str) -> str:
    if marker in text:
        return text
    count = text.count(closing_tag)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {closing_tag!r}, found {count}")
    return text.replace(closing_tag, payload.rstrip() + "\n" + closing_tag, 1)

def patch_text(text: str) -> str:
    text = inject_once(text, CSS_MARKER, CSS, "</style>")
    text = inject_once(text, JS_MARKER, JS, "</body>")
    return text

def main() -> int:
    original = BASE.read_text(encoding="utf-8")
    patched = patch_text(original)
    if patched != original:
        BASE.write_text(patched, encoding="utf-8", newline="\n")
    print("EZSTUDIO_NAV_ACTIVE_R3A3_MIGRATION_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
