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
        "AI/Robotics": "BOTZ",
        "Semiconductor": "SMH",
        "Quantum": "QTUM",
        "Space": "UFO",
        "Cloud": "SKYY",
        "Cybersecurity": "CIBR",
        "Clean Energy": "ICLN",
        "Biotech": "IBB"
    }
    
    report_data = []
    for theme, ticker in theme_etfs.items():
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period="5d")
            if len(hist) < 2: continue
            
            price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            vol_avg = hist['Volume'].iloc[:-1].mean()
            vol_today = hist['Volume'].iloc[-1]
            vol_ratio = vol_today / vol_avg if vol_avg > 0 else 1
            
            report_data.append({
                "Type": "Theme",
                "Name": theme,
                "Ticker": ticker,
                "Change": f"{price_change:.2f}%",
                "VolRatio": f"{vol_ratio:.2f}x"
            })
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

    try:
        trending = yf.Search("Trending", max_results=10).quotes
        for stock in trending:
            symbol = stock.get('symbol')
            if not symbol: continue
            s = yf.Ticker(symbol)
            h = s.history(period="2d")
            if len(h) < 2: continue
            
            change = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            if abs(change) > 3:
                report_data.append({
                    "Type": "Stock",
                    "Name": symbol,
                    "Ticker": symbol,
                    "Change": f"{change:.2f}%",
                    "VolRatio": "Trending"
                })
    except Exception as e:
        print(f"Error fetching trending stocks: {e}")
        
    return report_data

def summarize_with_gemini(data):
    if not GEMINI_API_KEY:
        return "Gemini API 키가 없습니다."
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    아래 미국 주식 시장 데이터를 바탕으로 한국 투자자를 위한 요약 리포트를 작성해줘.
    
    데이터:
    {data}
    
    조건:
    1. 현재 가장 핫한 테마 분석.
    2. 상승/하락 배경 설명.
    3. 향후 주목할 흐름 제언.
    4. 친절한 한국어 사용.
    """
    
    # 여러 모델과 재시도 로직
    models = ['gemini-1.5-flash', 'gemini-2.0-flash'] # 1.5가 보통 할당량이 더 여유롭습니다.
    
    for model_id in models:
        for attempt in range(3): # 최대 3번 재시도
            try:
                print(f"Attempting {model_id} (Attempt {attempt+1})...")
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                if response.text:
                    return response.text
            except Exception as e:
                print(f"Error with {model_id}: {e}")
                if "429" in str(e): # 할당량 초과 시 대기
                    print("Quota exceeded. Waiting 10 seconds...")
                    time.sleep(10)
                else:
                    break # 다른 에러면 다음 모델로
                    
    return f"AI 요약 실패. 원본 데이터 송부: {data}"

def send_email(content):
    if not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]):
        return

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
    except Exception as e:
        print(f"이메일 발송 실패: {e}")

if __name__ == "__main__":
    data = get_market_data()
    summary = summarize_with_gemini(data)
    send_email(summary)
