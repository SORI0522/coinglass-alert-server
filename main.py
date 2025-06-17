# main.py
import requests, time
from datetime import datetime

API_KEY = "당신의_API_KEY"
WEBHOOK_URL = "https://coinglass-alert-server.onrender.com/alert"
SYMBOLS = ["BTC", "ETH", "SOL"]
INTERVAL = "m5"
headers = {"accept": "application/json", "CG-API-KEY": API_KEY}

def get_alerts(symbol):
    alerts = []
    try:
        # Top 계정 롱/숏 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/top-long-short-account-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        now, prev = r["data"][-1], r["data"][-2]
        change = now["top_account_long_percent"] - prev["top_account_long_percent"]
        if abs(change) >= 3:
            alerts.append(f"{symbol} Top 계정 비율 급변: {change:.2f}%")

        # Taker 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/taker-buy-sell-volume/exchange-list?symbol={symbol}&range={INTERVAL}", headers=headers).json()
        ratio = r["data"]["buy_ratio"]
        if ratio >= 55 or ratio <= 45:
            alerts.append(f"{symbol} Taker Buy Ratio 이상치: {ratio:.2f}%")

        # 대형 청산
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/liquidation/order?exchange=Binance&symbol={symbol}&min_liquidation_amount=100000", headers=headers).json()
        if r["data"]:
            largest = max([x["usd_value"] for x in r["data"]])
            alerts.append(f"{symbol} 대형 청산 발생: ${largest:,.0f}")
    except:
        pass
    return alerts

def send_alert(msg):
    try:
        requests.post(WEBHOOK_URL, data=msg)
    except:
        pass

while True:
    for sym in SYMBOLS:
        msgs = get_alerts(sym)
        for m in msgs:
            send_alert(m)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 체크 완료")
    time.sleep(300)  # 5분마다 반복
