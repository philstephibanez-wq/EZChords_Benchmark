from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"templates"/"base.html.twig"

NAV = '{% set route_name = app.request.attributes.get(\'_route\') %}\n{% set current_song_id =\n  (selected_song is defined and selected_song ? selected_song.id :\n   (run is defined and run and run.song_id is defined ? run.song_id : app.request.query.get(\'song\')))\n%}\n<nav class="main-nav" aria-label="Pipeline">\n  <a href="{{ path(\'workbench_import\', current_song_id ? {song:current_song_id} : {}) }}"\n     class="{{ route_name == \'workbench_import\' ? \'active\' : \'\' }}"\n     {% if route_name == \'workbench_import\' %}aria-current="page"{% endif %}>Import</a>\n  <a href="{{ path(\'workbench_stems\', current_song_id ? {song:current_song_id} : {}) }}"\n     class="{{ route_name == \'workbench_stems\' ? \'active\' : \'\' }}"\n     {% if route_name == \'workbench_stems\' %}aria-current="page"{% endif %}>Stems</a>\n  <a href="{{ path(\'workbench_chords\', current_song_id ? {song:current_song_id} : {}) }}"\n     class="{{ route_name in [\'workbench_chords\',\'bench_view\'] ? \'active\' : \'\' }}"\n     {% if route_name in [\'workbench_chords\',\'bench_view\'] %}aria-current="page"{% endif %}>Chords</a>\n  <a href="{{ path(\'workbench_lyrics\', current_song_id ? {song:current_song_id} : {}) }}"\n     class="{{ route_name == \'workbench_lyrics\' ? \'active\' : \'\' }}"\n     {% if route_name == \'workbench_lyrics\' %}aria-current="page"{% endif %}>Lyrics</a>\n  <a href="{{ path(\'workbench_runs\', current_song_id ? {song:current_song_id} : {}) }}"\n     class="{{ route_name in [\'workbench_runs\',\'lab_run\'] ? \'active\' : \'\' }}"\n     {% if route_name in [\'workbench_runs\',\'lab_run\'] %}aria-current="page"{% endif %}>Runs</a>\n</nav>'

def main():
    text=BASE.read_text(encoding="utf-8")

    text=re.sub(
        r'<a class="brand" href="\{\{\s*path\(\'lab_index\'\)\s*\}\}">',
        '<a class="brand" href="{{ path(\'workbench_home\') }}">',
        text,
        count=1,
    )

    text,count=re.subn(
        r'(?s)<nav class="main-nav" aria-label="Pipeline">.*?</nav>',
        NAV,
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError("main-nav block not found exactly once")

    text=re.sub(
        r'(?s)<script>\s*/\*\s*EZSTUDIO_NAV_ACTIVE_R3A3_JS\s*\*/.*?</script>\s*',
        '',
        text,
        count=1,
    )

    BASE.write_text(text,encoding="utf-8",newline="\n")
    print("EZSTUDIO_WORKBENCH_NAV_R3B1_MIGRATION_OK")

if __name__=="__main__":
    main()
