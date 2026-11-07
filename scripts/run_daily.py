"""오케스트레이션: 에피소드 생성, 단계 상태 관리, 다음 할 일 안내.

python scripts/run_daily.py start [--slug weather-whiplash]
python scripts/run_daily.py status [에피소드]
python scripts/run_daily.py mark <단계> done|failed [--note 이유] [--ep 에피소드]
"""
import argparse
import sys
from common import STEPS, MAX_ATTEMPTS, EPISODES, today, read_json, write_json, log, find_episode

NEXT = {
    "pick": "웹 검색으로 candidates.json 작성 → python scripts/pick_topic.py {ep}",
    "script": "references/script-template.md 대로 {ep}/script.json 작성",
    "check": "python scripts/check.py script {ep}",
    "build": "python scripts/build_project.py {ep} → cd {ep}/video && npx hyperframes check --json",
    "render": "cd {ep}/video && npx hyperframes render --quality delivery --output ../short.mp4",
    "verify": "python scripts/check.py video {ep} + 스냅샷 확인",
    "approve": "사람에게 영상·제목·설명을 보여 주고 승인받기 (승인 시 {ep}/APPROVED 생성)",
    "upload": "python scripts/upload.py {ep}  (실제 업로드는 --live)",
    "record": "업로드 24h·72h 뒤 python scripts/analytics.py record --ep {ep} --views N --avg-view-pct P",
}


def status_path(ep):
    return ep / "status.json"


def cmd_start(a):
    slug = a.slug or "untitled"
    ep = EPISODES / f"{today()}-{slug}"
    if status_path(ep).exists():
        print(f"이미 있음: {ep}")
    else:
        write_json(status_path(ep), {"episode": ep.name, "steps": {s: {"state": "pending", "attempts": 0} for s in STEPS}})
        log(ep, "start")
        print(f"생성: {ep}")
    show(ep)


def show(ep):
    st = read_json(status_path(ep))
    print(f"\n[{st['episode']}]")
    nxt = None
    for s in STEPS:
        info = st["steps"][s]
        mark = {"done": "✔", "failed": "✘", "pending": "·"}[info["state"]]
        note = f" — {info['note']}" if info.get("note") else ""
        print(f"  {mark} {s:<8} (시도 {info['attempts']}){note}")
        if nxt is None and info["state"] != "done":
            nxt = s
    if nxt is None:
        print("\n모든 단계 완료.")
        return
    info = st["steps"][nxt]
    if info["state"] == "failed" and info["attempts"] >= MAX_ATTEMPTS:
        print(f"\n멈춤: '{nxt}' 단계가 {info['attempts']}번 실패했습니다. 사람에게 원인을 알리세요.")
        sys.exit(2)
    print(f"\n다음: {nxt} → " + NEXT[nxt].format(ep=f"episodes/{ep.name}"))


def cmd_status(a):
    show(find_episode(a.ep))


def cmd_mark(a):
    ep = find_episode(a.ep)
    st = read_json(status_path(ep))
    if a.step not in STEPS:
        raise SystemExit(f"알 수 없는 단계: {a.step}")
    idx = STEPS.index(a.step)
    undone = [s for s in STEPS[:idx] if st["steps"][s]["state"] != "done"]
    if a.result == "done" and undone:
        raise SystemExit(f"앞 단계가 끝나지 않았습니다: {', '.join(undone)}")
    if a.step == "approve" and a.result == "done" and not (ep / "APPROVED").exists():
        raise SystemExit("APPROVED 파일이 없습니다. 사람 승인 없이 approve를 완료할 수 없습니다.")
    info = st["steps"][a.step]
    info["attempts"] += 1
    info["state"] = a.result
    info["note"] = a.note or ""
    write_json(status_path(ep), st)
    log(ep, "mark", step=a.step, result=a.result, note=a.note)
    show(ep)


p = argparse.ArgumentParser()
sub = p.add_subparsers(dest="cmd", required=True)
s = sub.add_parser("start"); s.add_argument("--slug"); s.set_defaults(f=cmd_start)
s = sub.add_parser("status"); s.add_argument("ep", nargs="?"); s.set_defaults(f=cmd_status)
s = sub.add_parser("mark"); s.add_argument("step"); s.add_argument("result", choices=["done", "failed"])
s.add_argument("--note"); s.add_argument("--ep"); s.set_defaults(f=cmd_mark)
a = p.parse_args()
a.f(a)
