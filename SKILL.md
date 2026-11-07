---
name: daily-shorts
description: 매일 한 편씩 30초 세로 쇼츠(키네틱 타이포)를 기획·제작·검증·업로드하고, 성과를 기록해 다음 날 주제 선정에 반영하는 워크플로우. "오늘 쇼츠 만들어줘", "데일리 쇼츠 돌려줘", "쇼츠 성과 기록해줘"처럼 쇼츠를 정기적으로 만들거나 올리거나 성과를 정리할 때 사용한다.
---

# daily-shorts — 알고리즘의 선택을 기다리며

하루 한 편, 같은 순서로 만든다. 순서를 건너뛰지 않고, 각 단계는 `scripts/run_daily.py`가 기록한 상태에서 이어간다.
영상 제작은 HyperFrames(`/hyperframes`, `/hyperframes-cli`)로 한다.

## 시작할 때

1. `python scripts/run_daily.py status` 로 오늘 에피소드의 진행 단계를 확인한다. 없으면 `python scripts/run_daily.py start` 로 만든다.
2. `references/channel.md`(채널 정체성·톤·금지 사항)를 읽는다. 대본을 쓰기 전에 매번 읽는다.
3. 상태 파일이 가리키는 다음 단계부터 진행한다. 끝난 단계는 다시 하지 않는다.

## 단계

| # | 단계 | 하는 일 | 완료 조건 |
|---|---|---|---|
| 1 | pick | 웹 검색으로 오늘의 후보 5개를 `candidates.json`에 쓰고 `python scripts/pick_topic.py` 로 점수를 매긴다 | `topic.json` 생성 |
| 2 | script | `references/script-template.md` 규칙대로 `script.json`을 쓴다 | 파일 존재 |
| 3 | check | `python scripts/check.py script <에피소드>` | 오류 0개 |
| 4 | build | `python scripts/build_project.py <에피소드>` → HyperFrames 프로젝트 생성, `npx hyperframes check --json` 오류 0개 | `video/` 생성, check 통과 |
| 5 | render | `video/`에서 `npx hyperframes render --quality delivery --output ../short.mp4` | `short.mp4` 존재 |
| 6 | verify | `python scripts/check.py video <에피소드>` (길이·해상도), 스냅샷 3장 눈으로 확인 | 오류 0개 |
| 7 | approve | 사람에게 영상과 제목·설명을 보여 주고 승인받는다. 승인 시 `APPROVED` 파일 생성 | `APPROVED` 존재 |
| 8 | upload | `python scripts/upload.py <에피소드>` (기본은 dry-run, 실제는 `--live`) | `upload.json` 생성 |
| 9 | record | 24시간·72시간 뒤 `python scripts/analytics.py record ...` | history에 성과 기록 |

각 단계가 끝나면 `python scripts/run_daily.py mark <단계> done`, 실패하면 `mark <단계> failed --note "<이유>"`.

## 규칙 (가드레일)

- **사람 승인 없이 업로드하지 않는다.** `APPROVED` 파일은 사람이 "올려"라고 말한 뒤에만 만든다. 에이전트가 스스로 승인하지 않는다.
- **하루 1편.** `upload.py`가 같은 날 두 번째 업로드를 거부한다. 우회하지 않는다.
- **숫자에는 출처.** 대본에 숫자가 있으면 `sources`에 기사 URL을 넣는다. 확인 못 한 수치는 쓰지 않는다.
- **14일 안에 같은 주제 금지.** `pick_topic.py`가 제외한다.
- **음원·이미지 저작권.** 출처를 알 수 없는 음원·이미지를 쓰지 않는다. 음원이 필요하면 `/media-use`로 무료·라이선스 확인된 것만.
- **비밀값.** YouTube 인증 파일과 토큰은 `.secrets/`에만 둔다. 커밋하거나 대화에 출력하지 않는다.
- 실패한 단계는 같은 방법으로 2번까지만 재시도한다. 세 번째는 `failed`로 기록하고 사람에게 알린다.

## 끝낼 때

- 오늘 진행한 단계와 다음 할 일을 한 줄로 보고한다(`run_daily.py status` 출력 그대로 요약).
- 업로드했으면 영상 URL과 성과 기록 예정 시각(24h, 72h)을 알린다.

## 파일

- `references/channel.md` — 채널 정체성, 톤, 디자인, 금지 사항
- `references/script-template.md` — 30초 대본 구조와 `script.json` 형식
- `references/checklist.md` — 검사 항목 전체와 기준값
- `references/workflow.md` — 매일 실행 방법(예약 실행), 실패 복구
- `scripts/` — 단계별 도구 (Python 표준 라이브러리만 사용, 업로드만 Google API 라이브러리 필요)
- `templates/kinetic.css` — 키네틱 타이포 스타일
- `state/` — 주제·성과 누적 기록 (`history.jsonl`, `weights.json`)
- `examples/2026-10-30-weather/` — 예시 에피소드
