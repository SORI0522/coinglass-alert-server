# main.py
import requests, time
from datetime import datetime

API_KEY = "c85b840453a5460bb16a5fa8a6e217f3"
WEBHOOK_URL = "https://coinglass-alert-server.onrender.com/alert"
SYMBOLS = ["BTC", "ETH", "SOL", "XRP", "HYPE", "DOGE", "SUI", "ADA", "1000PEPE"]
INTERVAL = "m5"
headers = {"accept": "application/json", "CG-API-KEY": API_KEY}

def get_alerts(symbol):
    alerts = []

    try:
        # 1. Top 계정 롱숏 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/top-long-short-account-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now, prev = r["data"][-1], r["data"][-2]
            change = now["top_account_long_percent"] - prev["top_account_long_percent"]
            if abs(change) >= 2:
                alerts.append(f"{symbol} Top 계정 비율 급변: {change:+.2f}%")

        # 2. Top 포지션 롱숏 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/top-long-short-position-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now, prev = r["data"][-1], r["data"][-2]
            change = now["top_position_long_percent"] - prev["top_position_long_percent"]
            if abs(change) >= 2:
                alerts.append(f"{symbol} Top 포지션 비율 급변: {change:+.2f}%")

        # 3. 글로벌 계정 롱숏 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now, prev = r["data"][-1], r["data"][-2]
            change = now["global_account_long_percent"] - prev["global_account_long_percent"]
            if abs(change) >= 2:
                alerts.append(f"{symbol} 글로벌 계정 비율 변화: {change:+.2f}%")

        # 4. Taker 매수/매도 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/taker-buy-sell-volume/exchange-list?symbol={symbol}&range={INTERVAL}", headers=headers).json()
        if "data" in r and "buy_ratio" in r["data"]:
            buy = r["data"]["buy_ratio"]
            if buy >= 55 or buy <= 45:
                bias = "롱 우세 📈" if buy >= 55 else "숏 우세 📉"
                alerts.append(f"{symbol} Taker Buy 이상치: {buy:.2f}% → {bias}")

        # 5. 청산 총합
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/liquidation/aggregated-history?exchange_list=Binance&symbol={symbol}&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now, prev = r["data"][-1], r["data"][-2]
            long_liq = now["aggregated_long_liquidation_usd"] - prev["aggregated_long_liquidation_usd"]
            short_liq = now["aggregated_short_liquidation_usd"] - prev["aggregated_short_liquidation_usd"]
            if long_liq > 200000 or short_liq > 200000:
                alerts.append(f"{symbol} 청산 총합 변화 - 롱: ${long_liq:,.0f}, 숏: ${short_liq:,.0f}")
       

    except Exception as e:
        alerts.append(f"⚠️ {symbol} 데이터 오류: {e}")

    return alerts

def send_alert(msg):
    try:
        requests.post(WEBHOOK_URL, data=msg)
    except:
        pass

def start_monitor():
    while True:
        for sym in SYMBOLS:
            msgs = get_alerts(sym)
            for m in msgs:
                print(f"📩 {m}")
                send_alert(m)
                send_discord_alert(m)     # 디스코드 알림 전송
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 체크 완료")  # ← 이 줄 들여쓰기 위치 주의!
        time.sleep(300)


DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1384457126532878438/r35TL3ibVrDLQWHxuKxMzemkoHmxIscCwGyZxULzWnxuUd_FjkaJ3zGhfyhd4XF9T0nC"

def send_discord_alert(message):
    payload = {
        "content": f"@everyone\n📢 {message}"
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if r.status_code != 204:
            print(f"[❗] Discord 전송 실패: {r.status_code} / {r.text}")
        else:
            print("[✅] Discord 알림 전송 성공")
    except Exception as e:
        print(f"[🚨] Discord 전송 에러: {e}")

