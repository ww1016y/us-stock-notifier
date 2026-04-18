import yfinance as yf
import pandas as pd
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import datetime

# --- 설정 (환경 변수에서 가져옴) ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

# --- 1. 데이터 수집 함수 ---
def get_market_data():
    # 주요 테마/섹터 ETF 리스트 (AI, 반도체, 양자, 스페이스 등)
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
    
    # 1.1 섹터별 성과 분석
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

    # 1.2 거래량 급증 개별 종목 (S&P 500 내 일부 예시 또는 Trending)
    # 실제로는 더 넓은 범위를 탐색할 수 있으나, API 제한을 고려해 Trending Tickers 사용 권장
    try:
        trending = yf.Search("Trending", max_results=10).quotes
        for stock in trending:
            symbol = stock.get('symbol')
            if not symbol: continue
            s = yf.Ticker(symbol)
            h = s.history(period="2d")
            if len(h) < 2: continue
            
            change = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
            # 가격 상승과 거래량 동반 종목 필터링 (간이 예시)
            if change > 3: # 3% 이상 상승 종목만
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

# --- 2. Gemini를 이용한 한국어 요약 ---
def summarize_with_gemini(data):
    if not GEMINI_API_KEY:
        return "Gemini API 키가 설정되지 않았습니다. 데이터를 텍스트로 대체합니다: " + str(data)
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 모델 리스트 시도 (안정적인 모델 우선순위)
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    prompt = f"""
    아래는 오늘 미국 주식 시장의 섹터별 성과와 거래량이 급증한 종목 데이터야.
    이 데이터를 바탕으로 한국 주식 투자자가 이해하기 쉽게 한국어로 시장 동향을 요약해줘.
    
    조건:
    1. 현재 가장 '핫한' 테마가 무엇인지 분석할 것.
    2. 왜 해당 종목/테마가 올랐는지 뉴스나 시장 배경을 추측해서 설명해줄 것 (예: AI 수요 증가, 금리 동결 등).
    3. '미리 알고 선점하기' 위해 주목해야 할 다음 흐름을 제언할 것.
    4. 친절하고 전문적인 어조를 사용할 것.
    
    데이터:
    {data}
    """

    for model_name in models_to_try:
        try:
            print(f"Trying model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
            
    return "모든 Gemini 모델 호출에 실패했습니다. 데이터를 수동으로 확인하세요: " + str(data)

# --- 3. 이메일 발송 ---
def send_email(content):
    if not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]):
        print("이메일 설정 정보가 부족합니다.")
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"[{datetime.date.today()}] 미 증시 섹터 및 테마 분석 리포트"
    
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("이메일 발송 성공!")
    except Exception as e:
        print(f"이메일 발송 실패: {e}")

# --- 실행 ---
if __name__ == "__main__":
    print("데이터 수집 중...")
    market_data = get_market_data()
    
    print("Gemini 요약 생성 중...")
    summary = summarize_with_gemini(market_data)
    
    print("이메일 발송 중...")
    send_email(summary)
    print("모든 작업 완료!")
