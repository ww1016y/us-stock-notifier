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
            report.append(f"{name}({t}): {change:.2f}%")
        except: continue
    return "\n".join(report)

def summarize_with_gemini_direct(data):
    """라이브러리를 쓰지 않고 구글 서버에 직접 HTTP 요청을 보냅니다."""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": f"다음 주식 데이터를 한국어로 요약해줘:\n{data}"}]
        }]
    }
    
    try:
        print("Sending direct HTTP request to Google Gemini API (v1)...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        if response.status_code == 200:
            # 성공 시 텍스트 추출
            summary = res_json['candidates'][0]['content']['parts'][0]['text']
            print("SUCCESS: AI Summary generated!")
            return summary
        else:
            print(f"FAILED: Status {response.status_code}")
            print(f"Server Response: {res_json}")
            return None
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return None

def send_email(content):
    if not content or not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]): return
    msg = MIMEMultipart()
    msg['From'] = f"US Stock Notifier <{EMAIL_USER}>"
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"[{datetime.date.today()}] 미 증시 리포트 (최종 성공)"
    msg.attach(MIMEText(content, 'plain'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email Sent!")
    except Exception as e: print(f"Email Failed: {e}")

if __name__ == "__main__":
    print("Collecting data...")
    market_data = get_market_data()
    
    print("Requesting AI Summary (Direct HTTP)...")
    summary = summarize_with_gemini_direct(market_data)
    
    if summary:
        print("Sending email...")
        send_email(summary)
    else:
        print("Process aborted due to AI failure. Check logs.")
