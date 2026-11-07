"""검증 게이트.

python scripts/check.py script <에피소드>   대본 규칙 검사
python scripts/check.py video  <에피소드>   렌더 결과 검사 (ffprobe 필요)
오류가 있으면 종료 코드 1.
"""
import re
import sys
import json
import shutil
import subprocess
import datetime as dt
from common import read_json, read_history, find_episode, log

BANNED = ["역대급", "충격", "무조건", "실화냐", "소름"]
LINE_MAX = 12


def check_script(ep):
    s = read_json(ep / "script.json")
    if s is None:
        return [f"{ep}/script.json 없음"], []
    err, warn = [], []
    beats = s.get("beats", [])
    total = sum(b.get("duration", 0) for b in beats)
    if not 28 <= total <= 32:
        err.append(f"총 길이 {total}초 (28~32초)")
    if beats and beats[0].get("duration", 0) > 3:
        err.append(f"훅(첫 비트) {beats[0]['duration']}초 (3초 이하)")
    if not 7 <= len(beats) <= 12:
        warn.append(f"비트 {len(beats)}개 (권장 7~12개)")
    has_number = False
    for i, b in enumerate(beats, 1):
        d, lines = b.get("duration", 0), b.get("lines", [])
        if not 2 <= d <= 4:
            err.append(f"비트{i} 길이 {d}초 (2~4초)")
        if not 1 <= len(lines) <= 3:
            err.append(f"비트{i} 줄 수 {len(lines)} (1~3줄)")
        for ln in lines:
            if len(ln) > LINE_MAX:
                err.append(f"비트{i} '{ln}' {len(ln)}자 ({LINE_MAX}자 이내)")
            if re.search(r"\d", ln):
                has_number = True
            for w in BANNED:
                if w in ln:
                    warn.append(f"비트{i} 금지 표현 '{w}'")
        em = b.get("emphasis")
        if em and not any(em in ln for ln in lines):
            err.append(f"비트{i} 강조어 '{em}'가 줄에 없음")
        if b.get("style", "rise") not in ("slam", "rise", "split"):
            err.append(f"비트{i} style '{b.get('style')}' (slam|rise|split)")
    srcs = s.get("sources", [])
    if has_number and not srcs:
        err.append("숫자가 있는데 sources 없음")
    for src in srcs:
        if not str(src.get("url", "")).startswith(("http://", "https://")):
            err.append(f"출처 URL 형식 오류: {src}")
    title = s.get("title", "")
    if not title or len(title) > 40:
        err.append(f"제목 {len(title)}자 (1~40자)")
    tags = s.get("hashtags", [])
    if not 3 <= len(tags) <= 5 or "#Shorts" not in tags:
        err.append(f"해시태그 {len(tags)}개, #Shorts 포함 필요 (3~5개)")
    cutoff = (dt.date.today() - dt.timedelta(days=14)).isoformat()
    for h in read_history():
        if h.get("date", "") >= cutoff and h.get("episode") != ep.name and (h.get("slug") == s.get("slug") or h.get("topic") == s.get("topic")):
            err.append(f"최근 14일 중복: {h.get('date')} {h.get('topic')}")
    return err, warn


def check_video(ep):
    s = read_json(ep / "script.json") or {}
    mp4 = ep / "short.mp4"
    if not mp4.exists() or mp4.stat().st_size == 0:
        return ["short.mp4 없음 또는 0바이트"], []
    if not shutil.which("ffprobe"):
        return ["ffprobe 없음: FFmpeg를 설치하세요"], []
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(mp4)],
                         capture_output=True, text=True)
    info = json.loads(out.stdout)
    w, h = info["streams"][0]["width"], info["streams"][0]["height"]
    dur = float(info["format"]["duration"])
    want = sum(b.get("duration", 0) for b in s.get("beats", []))
    err = []
    if (w, h) != (1080, 1920):
        err.append(f"해상도 {w}x{h} (1080x1920)")
    if abs(dur - want) > 0.5:
        err.append(f"길이 {dur:.2f}초 (대본 {want}초 ±0.5)")
    return err, ["스냅샷 0·15·29초를 눈으로 확인하세요 (npx hyperframes snapshot --at 0,15,29)"]


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("script", "video"):
        raise SystemExit(__doc__)
    ep = find_episode(sys.argv[2] if len(sys.argv) > 2 else None)
    err, warn = (check_script if sys.argv[1] == "script" else check_video)(ep)
    for e in err:
        print("✘ 오류:", e)
    for w in warn:
        print("! 경고:", w)
    print(f"\n{sys.argv[1]} 검사: 오류 {len(err)}개, 경고 {len(warn)}개")
    log(ep, f"check-{sys.argv[1]}", errors=err, warnings=warn)
    sys.exit(1 if err else 0)


main()
