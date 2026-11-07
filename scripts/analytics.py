"""성과 기록과 카테고리 가중치 갱신 (피드백 루프).

python scripts/analytics.py record --ep <에피소드> --views 1200 --avg-view-pct 64 [--at 24h|72h]
python scripts/analytics.py weights      history로 state/weights.json 다시 계산
python scripts/analytics.py report       최근 성과 요약

가중치 = 0.5 × (카테고리 평균 조회수 ÷ 최고 카테고리 평균) + 0.5 × (평균 시청 지속률 ÷ 100)
72h 기록이 있으면 72h를, 없으면 24h를 쓴다. 기록이 없는 카테고리는 0.5.
"""
import argparse
import datetime as dt
from collections import defaultdict
from common import read_json, write_json, read_history, append_history, find_episode, log, WEIGHTS

CATEGORIES = ["weather", "price", "season", "life", "tech"]


def latest_metrics():
    best = {}
    for h in read_history():
        if h.get("type") != "metrics":
            continue
        cur = best.get(h["episode"])
        if cur is None or (h["at"] == "72h" and cur["at"] != "72h"):
            best[h["episode"]] = h
    return list(best.values())


def recompute():
    by = defaultdict(list)
    for m in latest_metrics():
        by[m["category"]].append(m)
    means = {c: (sum(x["views"] for x in v) / len(v), sum(x["avg_view_pct"] for x in v) / len(v)) for c, v in by.items()}
    top = max((mv for mv, _ in means.values()), default=0) or 1
    w = {c: 0.5 for c in CATEGORIES}
    for c, (mv, pct) in means.items():
        w[c] = round(0.5 * mv / top + 0.5 * pct / 100, 3)
    write_json(WEIGHTS, w)
    return w


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--ep"); r.add_argument("--views", type=int, required=True)
    r.add_argument("--avg-view-pct", type=float, required=True); r.add_argument("--at", default="24h", choices=["24h", "72h"])
    sub.add_parser("weights"); sub.add_parser("report")
    a = p.parse_args()
    if a.cmd == "record":
        ep = find_episode(a.ep)
        s = read_json(ep / "script.json")
        append_history({"type": "metrics", "date": dt.date.today().isoformat(), "episode": ep.name, "slug": s["slug"],
                        "topic": s["topic"], "category": s["category"], "at": a.at, "views": a.views,
                        "avg_view_pct": a.avg_view_pct})
        log(ep, "record", at=a.at, views=a.views, avg_view_pct=a.avg_view_pct)
        print("기록 완료. 갱신된 가중치:", recompute())
    elif a.cmd == "weights":
        print(recompute())
    else:
        rows = sorted(latest_metrics(), key=lambda m: m["date"])[-14:]
        if not rows:
            print("아직 성과 기록이 없습니다.")
        for m in rows:
            print(f"{m['date']}  {m['category']:<8} {m['views']:>7,}회  지속률 {m['avg_view_pct']:.0f}%  {m['topic']}")
        print("가중치:", read_json(WEIGHTS, {}))


main()
