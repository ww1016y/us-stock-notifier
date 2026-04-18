# 📈 미 증시 테마 및 섹터 분석 자동 알림 (US Stock Notifier)

이 프로젝트는 매일 미국 증시 마감 후, 시장의 주요 섹터 성과와 거래량 급증 종목을 분석하여 한국어로 요약된 리포트를 이메일로 발송합니다.

## 🚀 기능
1. **데이터 수집**: `yfinance`를 사용하여 주요 테마 ETF(AI, 반도체, 우주 등) 및 급등주 데이터 수집.
2. **AI 요약**: Gemini API를 사용하여 수집된 데이터를 한국어로 전문적으로 요약.
3. **자동화**: GitHub Actions를 통해 매일 아침 자동 실행.

## ⚙️ 설정 방법 (필독!)

프로젝트를 GitHub 리포지토리에 올린 후, 아래의 **Secrets**를 설정해야 합니다.

1. **GitHub 리포지토리** 접속 -> `Settings` -> `Secrets and variables` -> `Actions`
2. `New repository secret` 버튼을 눌러 아래 4개를 추가하세요.

| 이름 | 설명 | 비고 |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받은 API 키 | 무료 |
| `EMAIL_USER` | 알림을 보낼 Gmail 주소 | 발신용 |
| `EMAIL_PASS` | Gmail의 **앱 비밀번호** (16자리) | [설정방법](https://support.google.com/accounts/answer/185833) |
| `RECEIVER_EMAIL` | 리포트를 받을 이메일 주소 | 본인 메일 |

## 🛠️ 직접 실행해보기
GitHub 리포지토리의 `Actions` 탭에서 `Daily Stock Report` 워크플로우를 선택하고 `Run workflow`를 클릭하면 즉시 실행 결과를 확인할 수 있습니다.
