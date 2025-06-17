from flask import Flask, request

import threading
from main import start_monitor

app = Flask(__name__)

@app.route('/alert', methods=['POST'])
def alert():
    try:
        content_type = request.content_type
        print("📨 Content-Type:", content_type, flush=True)

        data = request.get_data(as_text=True)
        print("📩 TradingView 알림 수신:", data, flush=True)

        return '', 200
    except Exception as e:
        print("❌ 에러 발생:", e, flush=True)
        return 'Error', 500

# 기존 코드 아래쪽에 추가
if __name__ == '__main__':
    # ✅ Flask 서버 시작 + 감시 루프 백그라운드 실행
    threading.Thread(target=start_monitor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
