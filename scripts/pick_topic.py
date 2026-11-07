"""주제 선정: candidates.json 점수 매기기 → topic.json.

candidates.json (에이전트가 웹 검색 후 작성):
[{"topic": "10월 기온 급변", "slug": "weather-whiplash", "category": "weather",
  "trend": 0.9, "angle": "29.6℃ → 4℃", "sources": ["https://..."]}]

점수 = trend 0.5 + 카테고리 가중치 0.3 + 신선도 0.2. 14일 안에 다룬 주제는 제외.
"""
import sys
import datetime as dt
from common import read_json, write_json, read_history, WEIGHTS, find_episode, log

NOVELTY_DAYS = 14


def main():
    ep = find_episode(sys.argv[1] if len(sys.argv) > 1 else None)
    cands = read_json(ep / "candidates.json")
    if not cands:
        raise SystemExit(f"{ep}/candidates.json 이 없거나 비었습니다.")
    weights = read_json(WEIGHTS, {})
    hist = read_history()
    cutoff = (dt.date.today() - dt.timedelta(days=NOVELTY_DAYS)).isoformat()
    recent = [h for h in hist if h.get("date", "") >= cutoff]
    recent_slugs = {h.get("slug") for h in recent}
    recent_topics = {h.get("topic") for h in recent}
    recent_cats = [h.get("category") for h in recent]

    rows = []
    for c in cands:
        if c["slug"] in recent_slugs or c["topic"] in recent_topics:
            rows.append((None, c, f"제외: 최근 {NOVELTY_DAYS}일 안에 다룸"))
            continue
        if not c.get("sources"):
            rows.append((None, c, "제외: 출처 없음"))
            continue
        w = weights.get(c["category"], 0.5)
        novelty = 1 - min(recent_cats.count(c["category"]), 5) / 5
        score = 0.5 * float(c.get("trend", 0.5)) + 0.3 * w + 0.2 * novelty
        rows.append((round(score, 3), c, f"trend {c.get('trend')} · 가중치 {w} · 신선도 {novelty:.1f}"))

    rows.sort(key=lambda r: -1 if r[0] is None else r[0], reverse=True)
    print("순위  점수   주제")
    for i, (sc, c, why) in enumerate(rows, 1):
        print(f"{i:>2}.  {sc if sc is not None else '  - '}  {c['topic']} ({c['category']}) — {why}")
    best = next((c for sc, c, _ in rows if sc is not None), None)
    if not best:
        raise SystemExit("고를 수 있는 후보가 없습니다. 후보를 다시 찾으세요.")
    write_json(ep / "topic.json", best)
    log(ep, "pick", topic=best["topic"], slug=best["slug"])
    print(f"\n선택: {best['topic']} → {ep / 'topic.json'}")


main()
