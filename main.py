import yfinance as yf
import pandas as pd
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import datetime

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

def summarize_with_gemini(data):
    if not GEMINI_API_KEY: return "No API Key"
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # 가장 검증된 모델명 사용
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"다음 미국 주식 시장 데이터를 바탕으로 투자 리포트를 한국어로 짧게 작성해줘:\n{data}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI 요약 실패: {e}\n\n데이터:\n{data}"

def send_email(content):
    if not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]): return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"[{datetime.date.today()}] 미 증시 요약"
    msg.attach(MIMEText(content, 'plain'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email Sent!")
    except Exception as e: print(f"Email Failed: {e}")

if __name__ == "__main__":
    market_data = get_market_data()
    summary = summarize_with_gemini(market_data)
    send_email(summary)
    print("All Done!")
