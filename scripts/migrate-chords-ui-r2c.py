from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VIEW=ROOT/"templates"/"benchmark"/"view.html.twig"

STYLE_BLOCK=r"""
{% block styles %}
.review-check{display:flex!important;flex-direction:row!important;align-items:center;gap:6px!important;white-space:nowrap}
.display-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.display-controls label{display:flex;flex-direction:row;gap:6px;align-items:center}
.volume-control{display:flex!important;flex-direction:row!important;align-items:center;gap:6px!important}
.volume-control input[type=range]{width:120px;padding:0}
.player-panel{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.player-panel audio{min-width:min(620px,100%);max-width:100%}
.player-state{font-size:12px;color:#666;min-width:170px}
.timeline-line{display:grid;grid-template-columns:205px minmax(0,1fr) 185px;gap:10px;align-items:center;margin:10px 0}
.algo-name{font-weight:bold}
.timeline{display:flex;overflow-x:auto;border:1px solid #444;background:#fff;height:58px;scrollbar-width:thin;scroll-behavior:smooth}
.measure{min-width:auto;padding:0;border-right:2px solid #555;display:flex;flex-direction:column;box-sizing:border-box;font:13px Consolas,monospace;white-space:nowrap}
.measure .n{display:block;height:16px;padding:2px 6px;box-sizing:border-box;background:#eee;border-bottom:1px solid #bbb;font:9px Arial,sans-serif;color:#777}
.beats{display:flex;height:41px}
.beat{min-width:68px;padding:9px 8px 6px;box-sizing:border-box;border-right:1px solid #ccc;font:15px Consolas,monospace;text-align:center;white-space:nowrap;position:relative}
.beat:last-child{border-right:0}
.beat.current{outline:3px solid #111;outline-offset:-3px;background:#e8e8e8;font-weight:bold}
.measure.current-measure>.n{background:#d8d8d8;font-weight:bold}
.algo-tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.listen-button{padding:5px 9px}
.listen-radio{display:flex;flex-direction:row;gap:5px;align-items:center}
.choice{display:flex;gap:12px;align-items:center;justify-content:flex-end}
.choice label{display:flex;flex-direction:row;align-items:center;gap:4px}
@media(max-width:1100px){
  .timeline-line{grid-template-columns:180px minmax(0,1fr) 165px}
  .beat{min-width:62px}
}
@media(max-width:900px){
  .timeline-line{grid-template-columns:1fr}
  .choice{margin-bottom:8px;justify-content:flex-start}
}
{% endblock %}
"""

def main()->int:
    text=VIEW.read_text(encoding="utf-8")
    if "{% block styles %}" in text:
        print("EZSTUDIO_CHORDS_UI_R2C_ALREADY_PRESENT")
        return 0

    anchor="{% block body %}\n"
    if anchor not in text:
        raise RuntimeError(f"{VIEW}: body block anchor absent")

    text=text.replace(anchor, STYLE_BLOCK+"\n"+anchor, 1)
    VIEW.write_text(text, encoding="utf-8", newline="\n")
    print("EZSTUDIO_CHORDS_UI_R2C_MIGRATION_OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
