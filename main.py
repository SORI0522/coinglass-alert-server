import requests, time
from datetime import datetime, timedelta

API_KEY = "c85b840453a5460bb16a5fa8a6e217f3"
WEBHOOK_URL = "https://coinglass-alert-server.onrender.com/alert"
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1386628870320685167/CQrtC8B2MuDcJ0mXk6i9NeYBk6dRxD8I_bXyIdOgYsrOxk6dm8_DyhG2HiOJLD2hq2TQ"
SYMBOLS = ["BTC", "ETH", "SOL", "XRP"]
INTERVAL = "m5"
headers = {"accept": "application/json", "CG-API-KEY": API_KEY}

# 중복 알림 방지 캐시
last_sent_messages = {}

def should_send_alert(symbol, message):
    key = f"{symbol}-{message}"
    now = time.time()
    if key in last_sent_messages and now - last_sent_messages[key] < 600:
        return False
    last_sent_messages[key] = now
    return True

def get_alerts(symbol):
    alerts = []

    try:
        # 1. Top 계정 롱숏 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/top-long-short-account-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now_data, prev_data = r["data"][-1], r["data"][-2]
            change = now_data["top_account_long_percent"] - prev_data["top_account_long_percent"]
            if abs(change) >= 0.5:
                alerts.append(f"{symbol} Top 계정 비율 급변: {change:+.2f}%")

        # 2. Top 포지션 롱숏 비율 (완화 + 극단 조건 추가)
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/top-long-short-position-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now_data, prev_data = r["data"][-1], r["data"][-2]
            change = now_data["top_position_long_percent"] - prev_data["top_position_long_percent"]
            current = now_data["top_position_long_percent"]
            if abs(change) >= 0.1:
                alerts.append(f"{symbol} Top 포지션 비율 급변: {change:+.2f}%")
            
        # 3. 글로벌 계정 롱숏 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history?exchange=Binance&symbol={symbol}USDT&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now_data, prev_data = r["data"][-1], r["data"][-2]
            change = now_data["global_account_long_percent"] - prev_data["global_account_long_percent"]
            if abs(change) >= 0.5:
                alerts.append(f"{symbol} 글로벌 계정 비율 변화: {change:+.2f}%")

        # 4. Taker 매수/매도 비율
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/taker-buy-sell-volume/exchange-list?symbol={symbol}&range={INTERVAL}", headers=headers).json()
        if "data" in r and "buy_ratio" in r["data"]:
            buy = r["data"]["buy_ratio"]
            if buy >= 80 or buy <= 20:
                bias = "롱 우세 📈" if buy >= 55 else "숏 우세 📉"
                alerts.append(f"{symbol} Taker Buy 이상치: {buy:.2f}% → {bias}")

        # 5. 청산 총합
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/liquidation/aggregated-history?exchange_list=Binance&symbol={symbol}&interval={INTERVAL}", headers=headers).json()
        if "data" in r and len(r["data"]) >= 2:
            now_data, prev_data = r["data"][-1], r["data"][-2]
            long_liq = now_data["aggregated_long_liquidation_usd"] - prev_data["aggregated_long_liquidation_usd"]
            short_liq = now_data["aggregated_short_liquidation_usd"] - prev_data["aggregated_short_liquidation_usd"]
            if long_liq > 200000 or short_liq > 200000:
                alerts.append(f"{symbol} 청산 총합 변화 - 롱: ${long_liq:,.0f}, 숏: ${short_liq:,.0f}")

        # 6. 대형 청산 주문
        r = requests.get(f"https://open-api-v4.coinglass.com/api/futures/liquidation/order?exchange=Binance&symbol={symbol}&min_liquidation_amount=50000000", headers=headers).json()
        if "data" in r and len(r["data"]) > 0:
            liq = r["data"][0]
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

def send_discord_alert(message):
    payload = {"content": message}
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if r.status_code != 204:
            print(f"[❗] Discord 전송 실패: {r.status_code} / {r.text}")
        else:
            print(f"[✅] Discord 전송 성공: {message}")
    except Exception as e:
        print(f"[🚨] Discord 전송 에러: {e}")

def wait_until_next_interval():
    now = datetime.now()
    next_minute = ((now.minute // 5) + 1) * 5
    next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minute)
    wait_sec = (next_time - now).total_seconds()
    print(f"[⏳] 다음 5분 정각까지 {int(wait_sec)}초 대기 중...")
    time.sleep(wait_sec)

def start_monitor():
    while True:
        wait_until_next_interval()
        for sym in SYMBOLS:
            msgs = get_alerts(sym)
            for m in msgs:
                if should_send_alert(sym, m):
                    print(f"📩 {m}")
                    send_alert(m)
                    send_discord_alert(m)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 체크 완료")

if __name__ == "__main__":
    start_monitor()


