from flask import Flask, render_template, jsonify, request
import serial

app = Flask(__name__)

# 위험지역 리스트
danger_zones = []

# LoRa 초기화
lora = serial.Serial('/dev/serial0', 9600, timeout=1)

# 디바이스 마커용 예시 위치 (원하면 실시간 GPS로도 가능)
device_positions = {
    "pi1": {"lat": 37.5665, "lon": 126.9780},
    "pi2": {"lat": 37.5675, "lon": 126.9790},
    "pi3": {"lat": 37.5680, "lon": 126.9760}
}

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/locations')
def get_locations():
    return jsonify(device_positions)

@app.route('/dangers')
def get_dangers():
    return jsonify(danger_zones)

@app.route('/danger', methods=['POST'])
def add_danger():
    data = request.get_json()
    lat = data.get('lat')
    lon = data.get('lon')
    if lat and lon:
        danger_zones.append({'lat': lat, 'lon': lon})
        # LoRa로 위험지역 전송
        msg = f"DANGER:{lat},{lon}\n"
        lora.write(msg.encode())
        print(f"[+] 위험지역 전송됨: {msg.strip()}")
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'fail'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
