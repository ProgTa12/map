import math
import time
import gps
import serial
from gpiozero import PWMOutputDevice

motor_pins = [25, 26, 27, 14, 12, 13, 4, 15]
motors = [PWMOutputDevice(pin) for pin in motor_pins]

dangerLat, dangerLon = 35.6586, 139.7454
last_danger_update = time.time()
danger_interval = 30

danger_zones = [
    (35.6586, 139.7454),  # 도쿄타워
    (35.7100, 139.8107),  # 스카이트리
    (35.6895, 139.6917)   # 도쿄 시청
]
danger_index = 0

lora = serial.Serial('/dev/serial0', 9600, timeout=1)

def read_lora():
    global dangerLat, dangerLon
    try:
        if lora.in_waiting:
            line = lora.readline().decode().strip()
            lat, lon = map(float, line.split(','))
            dangerLat = lat
            dangerLon = lon
            print(f"LoRa 수신 위험지역: {dangerLat}, {dangerLon}")
    except Exception as e:
        print("LoRa 입력 파싱 실패:", e)

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def get_direction_index(bearing):
    if bearing >= 337.5 or bearing < 22.5:
        return 0
    elif bearing < 67.5:
        return 1
    elif bearing < 112.5:
        return 2
    elif bearing < 157.5:
        return 3
    elif bearing < 202.5:
        return 4
    elif bearing < 247.5:
        return 5
    elif bearing < 292.5:
        return 6
    else:
        return 7

def get_strength(distance):
    if distance < 20:
        return 1.0
    elif distance < 50:
        return 0.7
    elif distance < 100:
        return 0.4
    else:
        return 0.0

def vibrate(index, strength):
    for i in range(8):
        motors[i].value = strength if i == index else 0

session = gps.gps(mode=gps.WATCH_ENABLE)

try:
    while True:
        # LoRa로 위험지역 수신 여부 확인
        read_lora()

        # 자동 위험지역 순환 (테스트용)
        if time.time() - last_danger_update > danger_interval:
            danger_index = (danger_index + 1) % len(danger_zones)
            dangerLat, dangerLon = danger_zones[danger_index]
            last_danger_update = time.time()
            print(f"자동 갱신된 위험지역 → {dangerLat}, {dangerLon}")

        # GPS 위치 읽기
        report = session.next()
        if report['class'] == 'TPV':
            lat = getattr(report, 'lat', None)
            lon = getattr(report, 'lon', None)
            if lat is not None and lon is not None:
                dist = get_distance(lat, lon, dangerLat, dangerLon)
                bearing = get_bearing(lat, lon, dangerLat, dangerLon)
                direction = get_direction_index(bearing)
                strength = get_strength(dist)
                vibrate(direction, strength)
                print(f"{lat:.5f}, {lon:.5f} | 거리: {dist:.1f}m | 방위: {bearing:.1f}° | 방향: {direction} | 진동: {strength:.2f}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n종료: 진동 OFF")
    for m in motors:
        m.value = 0