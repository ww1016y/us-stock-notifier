import yfinance as yf
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import datetime
import json

# --- 설정 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def get_market_data():
    theme_etfs = {"AI": "BOTZ", "Chips": "SMH", "Space": "UFO", "Quantum": "QTUM"}
    report = []
    for name, t in theme_etfs.items():
        try:
            ticker = yf.Ticker(t)
            hist = ticker.history(period="2d")
            if len(hist) < 2: continue
            change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            report.append(f"| {name} | {t} | {change:.2f}% |")
        except: continue
    return "\n".join(report)

def summarize_with_gemini_ultra(data):
    """모든 경로와 모델을 순회하며 성공할 때까지 시도합니다."""
    combos = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-pro"),
        ("v1beta", "gemini-pro"),
        ("v1", "gemini-1.5-flash")
    ]
    
    payload = {
        "contents": [{"parts": [{"text": f"너는 주식 전문가야. 다음 데이터를 한국어로 아주 멋지게 요약해줘:\n{data}"}]}]
    }
    
    for version, model in combos:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            print(f"Trying {version} with {model}...")
            response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=15)
            if response.status_code == 200:
                print(f"SUCCESS! Found working combo: {version}/{model}")
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"Failed {version}/{model}: Status {response.status_code}")
        except Exception as e:
            print(f"Error calling {model}: {e}")
            continue
            
    return None

def send_email(content, is_ai=True):
    if not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]): return
    
    subject = f"[{datetime.date.today()}] 미 증시 분석 리포트"
    if not is_ai:
        subject += " (데이터 모드)"
    
    # 문법 에러 방지를 위해 replace는 밖에서 처리
    formatted_content = content.replace('\n', '<br>')
    
    html_content = f"""
    <html>
    <body>
        <h2>📈 오늘의 미국 증시 요약</h2>
        <p>{formatted_content}</p>
        <hr>
        <p style="color: grey;">※ 본 리포트는 AI 분석 또는 시장 데이터를 바탕으로 자동 생성되었습니다.</p>
    </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = f"Stock Assistant <{EMAIL_USER}>"
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email Sent Successfully!")
    except Exception as e:
        print(f"Email Failed: {e}")

if __name__ == "__main__":
    print("Process started...")
    raw_data = get_market_data()
    market_table = f"| 테마 | 티커 | 등락률 |\n| :--- | :--- | :--- |\n{raw_data}"
    
    print("AI 요약 시도 중...")
    summary = summarize_with_gemini_ultra(market_table)
    
    if summary:
        print("AI 요약 성공! 메일을 발송합니다.")
        send_email(summary, is_ai=True)
    else:
        print("AI 요약 실패. 데이터 표를 발송합니다.")
        # AI가 실패하면 데이터라도 보냄
        email_body = f"현재 AI 요약 기능 점검 중으로, 주식 데이터 표를 우선 보내드립니다.<br><br>{market_table}"
        send_email(email_body, is_ai=False)
        
    print("Process Finished.")
