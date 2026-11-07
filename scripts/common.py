"""공통 경로·기록 유틸. 모든 스크립트가 표준 라이브러리만 쓴다."""
import json
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
EPISODES = ROOT / "episodes"
HISTORY = STATE / "history.jsonl"
WEIGHTS = STATE / "weights.json"

STEPS = ["pick", "script", "check", "build", "render", "verify", "approve", "upload", "record"]
MAX_ATTEMPTS = 2


def today():
    return dt.date.today().isoformat()


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_history():
    if not HISTORY.exists():
        return []
    return [json.loads(l) for l in HISTORY.read_text(encoding="utf-8").splitlines() if l.strip()]


def append_history(row):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def log(ep_dir, event, **kw):
    row = {"at": dt.datetime.now().isoformat(timespec="seconds"), "event": event, **kw}
    with (Path(ep_dir) / "log.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def find_episode(arg=None):
    """에피소드 폴더 경로. 인자가 없으면 오늘 날짜로 시작하는 가장 최근 폴더."""
    if arg:
        p = Path(arg)
        return p if p.is_absolute() or p.exists() else EPISODES / arg
    hits = sorted(EPISODES.glob(today() + "*"))
    if not hits:
        raise SystemExit(f"오늘({today()}) 에피소드가 없습니다. run_daily.py start 를 먼저 실행하세요.")
    return hits[-1]
