"""script.json → HyperFrames 프로젝트(<에피소드>/video/).

python scripts/build_project.py <에피소드>
비트 하나가 장면(sub-composition) 하나. 1080x1920, 장면 순서대로 이어 붙인다.
"""
import sys
import html
import json
from common import ROOT, read_json, find_episode, log

W, H = 1080, 1920
TEXT_W = W - 80 - 140          # .stack 의 가용 폭
MAX_SIZE = 150
PALETTE = [("#111111", "#F2EFE9"), ("#F2EFE9", "#111111")]  # (배경, 글자)


def char_w(c):
    if "가" <= c <= "힣":
        return 1.0
    if c == " ":
        return 0.3
    return 0.62


def line_w(line, em):
    if em and em in line:
        before, after = line.split(em, 1)
        return sum(map(char_w, before + after)) + 1.6 * sum(map(char_w, em))
    return sum(map(char_w, line))


def line_html(line, em, color):
    if em and em in line:
        before, after = line.split(em, 1)
        return f'{html.escape(before)}<span class="em" style="color:{color}">{html.escape(em)}</span>{html.escape(after)}'
    return html.escape(line)


def scene(i, beat, accent, css):
    sid = f"b{i}"
    d = float(beat["duration"])
    lines, em = beat["lines"], beat.get("emphasis")
    style = beat.get("style", "rise")
    size = int(min(MAX_SIZE, TEXT_W / max(line_w(l, em) for l in lines)))
    bg, fg = PALETTE[i % 2]
    if style == "slam":
        bg, fg = accent, "#111111"
    em_color = fg if style == "slam" else accent
    rows = "\n".join(
        f'    <div id="{sid}-l{k}" class="line clip" data-start="0" data-duration="{d}">'
        f'<span class="t {sid}-t" style="color:{fg}">{line_html(l, em, em_color)}</span></div>'
        for k, l in enumerate(lines))
    if i == 1:   # 훅: 0프레임부터 글자가 보여야 한다(썸네일)
        enter = f'tl.fromTo(".{sid}-t", {{scale: 1.12, opacity: 1}}, {{scale: 1, opacity: 1, duration: 0.5, ease: "power3.out"}}, 0);'
    elif style == "slam":
        enter = (f'tl.fromTo(".{sid}-t", {{scale: 2.4, opacity: 0, filter: "blur(12px)"}}, '
                 f'{{scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.35, ease: "power4.out", stagger: 0.12}}, 0.05);\n'
                 f'    tl.fromTo(".{sid}-t .em", {{x: -10}}, {{x: 0, duration: 0.25, ease: "elastic.out(1, 0.3)"}}, 0.4);')
    elif style == "split":
        enter = (f'document.querySelectorAll(".{sid}-t").forEach((el, k) => '
                 f'tl.fromTo(el, {{x: k % 2 ? 700 : -700, opacity: 0}}, {{x: 0, opacity: 1, duration: 0.5, ease: "expo.out"}}, 0.05 + k * 0.1));')
    else:
        enter = (f'tl.fromTo(".{sid}-t", {{y: 120, opacity: 0}}, '
                 f'{{y: 0, opacity: 1, duration: 0.45, ease: "power3.out", stagger: 0.15}}, 0.05);')
    exit_at = max(d - 0.3, 0.6)
    return sid, d, f"""<template>
  <style>
{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="{W}" data-height="{H}">
    <div class="bg" style="background:{bg}"></div>
    <div class="stack" style="font-size:{size}px">
{rows}
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {enter}
    tl.fromTo(".{sid}-t", {{y: 0, opacity: 1}}, {{y: -60, opacity: 0, duration: 0.25, ease: "power2.in", immediateRender: false}}, {exit_at:.2f});
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""


def main():
    ep = find_episode(sys.argv[1] if len(sys.argv) > 1 else None)
    s = read_json(ep / "script.json")
    if not s:
        raise SystemExit(f"{ep}/script.json 없음")
    css = (ROOT / "templates" / "kinetic.css").read_text(encoding="utf-8")
    css = "\n".join("    " + l for l in css.splitlines())
    out = ep / "video"
    (out / "compositions").mkdir(parents=True, exist_ok=True)
    hosts, t = [], 0.0
    for i, beat in enumerate(s["beats"], 1):
        sid, d, body = scene(i, beat, s.get("accent", "#FF5A1F"), css)
        (out / "compositions" / f"{sid}.html").write_text(body, encoding="utf-8")
        hosts.append(f'      <div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
                     f'data-start="{t:g}" data-duration="{d:g}" data-track-index="1" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}"></div>')
        t += d
    index = f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8"><title>{html.escape(s.get('title', 'short'))}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
  </head>
  <body style="margin:0;background:#111">
    <div id="root" data-composition-id="main" data-start="0" data-duration="{t:g}" data-width="{W}" data-height="{H}">
{chr(10).join(hosts)}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
    (out / "index.html").write_text(index, encoding="utf-8")
    meta = {"title": s.get("title"), "description": s.get("description"), "hashtags": s.get("hashtags"), "duration": t}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log(ep, "build", scenes=len(hosts), duration=t)
    print(f"장면 {len(hosts)}개, {t:g}초 → {out}")
    print(f"다음: cd {out} && npx hyperframes lint && npx hyperframes check --json")


main()
