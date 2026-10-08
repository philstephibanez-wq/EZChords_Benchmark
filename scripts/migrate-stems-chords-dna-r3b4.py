from pathlib import Path
import os
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "templates" / "base.html.twig"

def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".r3b4.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def main() -> None:
    text = BASE.read_text(encoding="utf-8")

    # R3B2 navigation used workbench_chords. Only change the navigation destination.
    old = "path('workbench_chords', current_song_id ? {song:current_song_id} : {})"
    new = "path('lab_chords_experiment', current_song_id ? {song:current_song_id} : {})"

    if old in text:
        text = text.replace(old, new, 1)
    elif "path('lab_chords_experiment'" not in text:
        raise RuntimeError("CHORDS navigation anchor not found")

    # Active state must include the new workbench route and the canonical bench_view.
    text = text.replace(
        "route_name in ['workbench_chords','bench_view']",
        "route_name in ['lab_chords_experiment','bench_view']"
    )

    atomic_write(BASE, text)
    print("EZSTUDIO_STEMS_CHORDS_DNA_R3B4_NAV_OK")

if __name__ == "__main__":
    main()
