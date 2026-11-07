"""YouTube 업로드 (가드레일 포함).

python scripts/upload.py <에피소드>            dry-run: 검사만 하고 올릴 내용 출력
python scripts/upload.py <에피소드> --live     실제 업로드 (비공개 + 예약 공개)

필요: pip install google-api-python-client google-auth-oauthlib
인증: .secrets/client_secret.json (Google Cloud에서 사람이 직접 발급), 첫 실행 때 브라우저 로그인 → .secrets/token.json
"""
import sys
import argparse
import datetime as dt
from common import ROOT, read_json, write_json, read_history, append_history, find_episode, log

SECRETS = ROOT / ".secrets"
PUBLISH_HOUR = 18   # 예약 공개 시각(로컬)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def gate(ep, s):
    """업로드 전 가드레일. 하나라도 걸리면 업로드하지 않는다."""
    problems = []
    if not (ep / "APPROVED").exists():
        problems.append("APPROVED 파일 없음: 사람 승인이 필요합니다")
    st = read_json(ep / "status.json", {})
    for step in ("check", "verify"):
        if st.get("steps", {}).get(step, {}).get("state") != "done":
            problems.append(f"'{step}' 단계가 done 아님")
    if not (ep / "short.mp4").exists():
        problems.append("short.mp4 없음")
    today = dt.date.today().isoformat()
    if any(h.get("type") == "upload" and h.get("date") == today for h in read_history()):
        problems.append("오늘 이미 1편 업로드함 (하루 1편 제한)")
    if (ep / "upload.json").exists():
        problems.append("이 에피소드는 이미 업로드됨")
    return problems


def youtube_client():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise SystemExit("pip install google-api-python-client google-auth-oauthlib 가 필요합니다.")
    token = SECRETS / "token.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = SECRETS / "client_secret.json"
            if not secret.exists():
                raise SystemExit(f"{secret} 가 없습니다. 사람이 Google Cloud 콘솔에서 발급해 넣어야 합니다.")
            creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ep", nargs="?")
    p.add_argument("--live", action="store_true")
    a = p.parse_args()
    ep = find_episode(a.ep)
    s = read_json(ep / "script.json")
    problems = gate(ep, s)
    publish_at = dt.datetime.combine(dt.date.today(), dt.time(PUBLISH_HOUR)).astimezone()
    body = {
        "snippet": {
            "title": s["title"],
            "description": s.get("description", "") + "\n\n" + " ".join(s.get("hashtags", []))
                           + "\n\n출처\n" + "\n".join(x["url"] for x in s.get("sources", [])),
            "tags": [h.lstrip("#") for h in s.get("hashtags", [])],
            "categoryId": "22",
        },
        "status": {"privacyStatus": "private", "publishAt": publish_at.isoformat(), "selfDeclaredMadeForKids": False},
    }
    print("제목:", body["snippet"]["title"])
    print("공개 예약:", body["status"]["publishAt"])
    if problems:
        for x in problems:
            print("✘", x)
        log(ep, "upload-blocked", problems=problems)
        raise SystemExit(1)
    if not a.live:
        print("\n가드레일 통과. dry-run이라 올리지 않았습니다. 실제 업로드는 --live")
        log(ep, "upload-dry-run")
        return
    from googleapiclient.http import MediaFileUpload
    yt = youtube_client()
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(ep / "short.mp4"), chunksize=-1, resumable=True))
    res = req.execute()
    url = f"https://youtube.com/shorts/{res['id']}"
    write_json(ep / "upload.json", {"id": res["id"], "url": url, "publishAt": body["status"]["publishAt"]})
    append_history({"type": "upload", "date": dt.date.today().isoformat(), "episode": ep.name, "slug": s["slug"],
                    "topic": s["topic"], "category": s["category"], "video_id": res["id"]})
    log(ep, "upload", url=url)
    print("업로드 완료:", url)


main()
