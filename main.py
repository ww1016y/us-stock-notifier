import yfinance as yf
import google.generativeai as genai
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
    if not GEMINI_API_KEY: return "API Key Missing"
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # [중요] 모든 가능한 모델명 후보군
    # 구글 API 서버가 인식하는 명칭이 환경마다 다를 수 있어 순회합니다.
    model_names = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-pro',
        'models/gemini-1.5-flash',
        'models/gemini-pro'
    ]
    
    last_error = ""
    for name in model_names:
        try:
            print(f"Testing model: {name}...")
            model = genai.GenerativeModel(name)
            prompt = f"다음 미국 주식 시장 데이터를 한국어로 투자 리포트처럼 요약해줘:\n{data}"
            response = model.generate_content(prompt)
            
            # 응답이 성공적으로 왔는지 검증
            if response and response.text:
                print(f"SUCCESS with model: {name}!")
                return response.text
        except Exception as e:
            print(f"FAILED model {name}: {e}")
            last_error = str(e)
            continue
            
    return f"모든 모델 호출 실패. 최종 에러: {last_error}\n\n데이터:\n{data}"

def send_email(content):
    if not all([EMAIL_USER, EMAIL_PASS, RECEIVER_EMAIL]): return
    
    # [방어 로직] 만약 AI 요약이 실패했다면 이메일을 보내지 않고 제가 로그를 더 보게 합니다.
    if "모든 모델 호출 실패" in content:
        print("AI Summarization failed. Skipping email to prevent spamming errors.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"US Stock AI <{EMAIL_USER}>"
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"[{datetime.date.today()}] 미 증시 AI 분석 리포트 (성공)"
    msg.attach(MIMEText(content, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print("Email Sent Successfully!")
    except Exception as e:
        print(f"Email Failed: {e}")

if __name__ == "__main__":
    print("Step 1: Collecting Market Data...")
    market_data = get_market_data()
    
    print("Step 2: AI Summarizing (Testing all models)...")
    summary = summarize_with_gemini(market_data)
    
    print("Step 3: Sending Result...")
    send_email(summary)
    print("Process Finished.")
