from flask import Flask, request

app = Flask(__name__)

@app.route('/alert', methods=['POST'])
def alert():
    data = request.json
    print("📩 TradingView 알림 수신:", data)
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
