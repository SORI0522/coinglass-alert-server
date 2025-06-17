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
                alerts.append(f"{symbol} Taker Buy 이상치: {buy:.2f}%")

        # 5. 청산 총합
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/liquidation/aggregated-history?exchange_list=Binance&symbol={symbol}&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now, prev = r["data"][-1], r["data"][-2]
            long_liq = now["aggregated_long_liquidation_usd"] - prev["aggregated_long_liquidation_usd"]
            short_liq = now["aggregated_short_liquidation_usd"] - prev["aggregated_short_liquidation_usd"]
            if long_liq > 200000 or short_liq > 200000:
                alerts.append(f"{symbol} 청산 총합 변화 - 롱: ${long_liq:,.0f}, 숏: ${short_liq:,.0f}")

        # 6. 대형 청산 주문 (실시간 데이터)
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/liquidation/order?exchange=Binance&symbol={symbol}&min_liquidation_amount=100000", headers=headers).json()
        if "data" in r and len(r["data"]) > 0:
            for liq in r["data"]:
                usd = liq["usd_value"]
                price = liq["price"]
                side = "롱 강제청산" if liq["side"] == 2 else "숏 강제청산"
                alerts.append(f"{symbol} {side} 발생: ${usd:,.0f} @ {price}")

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
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 체크 완료")
        time.sleep(300)
