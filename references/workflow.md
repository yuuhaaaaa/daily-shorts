# 매일 실행과 복구

## 실행 시각
| 시각 | 할 일 |
|---|---|
| 매일 09:00 | `start` → pick → script → check → build → render → verify (에이전트) |
| 사람 확인 후 | approve → upload. 예약 공개 시각은 18:00(퇴근 시간대) |
| 업로드 +24h, +72h | record (성과 기록) |

### 예약 실행 방법
- **Claude Code 루틴**: `/schedule` 로 매일 09:00에 "daily-shorts 스킬로 오늘 쇼츠 진행해줘"를 등록한다.
- **Windows 작업 스케줄러**: 09:00에 아래 명령 실행.
  ```
  claude -p "daily-shorts 스킬로 오늘 쇼츠를 verify 단계까지 진행하고 결과를 보고해줘"
  ```
- 업로드는 예약 실행에 넣지 않는다. 승인은 항상 사람이 한다.

## 상태 파일
`episodes/<날짜>-<slug>/status.json` 에 단계별 상태(`pending`/`done`/`failed`), 시도 횟수, 메모가 남는다. 모든 기록은 같은 폴더 `log.jsonl` 에도 한 줄씩 쌓인다.

## 실패했을 때
| 단계 | 흔한 원인 | 조치 |
|---|---|---|
| pick | 검색 결과가 오래됨 | 날짜를 넣어 다시 검색, 후보는 최근 7일 기사만 |
| check | 줄이 12자 초과 | 단어를 줄인다. 글자 크기를 줄이지 않는다 |
| build | HyperFrames check 오류 | 출력의 `Fix:` 줄대로 고친다 |
| render | Chrome·FFmpeg 없음 | `npx hyperframes doctor --json`, `npx hyperframes browser ensure` |
| upload | 인증 만료 | `.secrets/token.json` 삭제 후 다시 인증 (사람이 직접) |

같은 단계가 2번 실패하면 멈추고 사람에게 원인과 함께 알린다.
