import yfinance as yf
import pandas as pd
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import datetime
import time

# --- 설정 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def get_market_data():
    theme_etfs = {
        "AI/Robotics": "BOTZ", "Semiconductor": "SMH", "Quantum": "QTUM",
        "Space": "UFO", "Cloud": "SKYY", "Cybersecurity": "CIBR",
        "Clean Energy": "ICLN", "Biotech": "IBB"
    }
    report_data = []
    for theme, ticker in theme_etfs.items():
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="5d")
            if len(hist) < 2: continue
            price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            report_data.append({"Type": "Theme", "Name": theme, "Ticker": ticker, "Change": f"{price_change:.2f}%"})
        except Exception as e: print(f"Error {ticker}: {e}")
    return report_data

def summarize_with_gemini(data):
    if not GEMINI_API_KEY: return "API Key Missing"
    
    try:
        # 버전 v1 명시 및 클라이언트 생성
        client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1'})
        
        prompt = f"다음 미국 주식 데이터를 한국어로 요약해줘: {data}"
        
        # 가장 안정적인 호출 방식
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"v1 attempt failed: {e}")
        return f"AI 요약 실패 (에러: {e})\n\n데이터: {data}"

def send_email(content):
    if not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]): return
    msg = MIMEMultipart()
    msg['From'] = f"US Stock Notifier <{EMAIL_USER}>"
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"[{datetime.date.today()}] 미 증시 분석 리포트"
    msg.attach(MIMEText(content, 'plain'))
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("이메일 발송 성공!")
    except Exception as e: print(f"이메일 발송 실패: {e}")

if __name__ == "__main__":
    data = get_market_data()
    summary = summarize_with_gemini(data)
    send_email(summary)
    print("Done!")
