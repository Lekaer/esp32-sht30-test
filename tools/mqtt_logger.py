import paho.mqtt.client as mqtt
import time

LOG = '/Users/kaka/IOT/mqtt_log.txt'
last = [None]
RECONNECTS = []

def log(line):
    with open(LOG, 'a') as f:
        f.write(line + '\n')
    print(line, flush=True)

def on_connect(c, u, f, rc):
    c.subscribe('esp32/sht30-kaka')
    log(f"\n=== {time.strftime('%H:%M:%S')} 订阅端上线/重连 ===")

def on_disconnect(c, u, rc):
    log(f"--- {time.strftime('%H:%M:%S')} 订阅端断线（rc={rc}），paho 将自动重连 ---")

def on_message(c, u, msg):
    now = time.time()
    ts = time.strftime('%H:%M:%S')
    payload = msg.payload.decode()
    flag = ''
    if last[0] is not None:
        dt = now - last[0]
        if dt > 6.5:
            flag = f'  <<缺口 {dt:.1f}s>>'
    last[0] = now
    log(f'{ts} {payload}{flag}')

c = mqtt.Client()
c.on_connect = on_connect
c.on_disconnect = on_disconnect
c.on_message = on_message
c.reconnect_delay_set(min_delay=1, max_delay=10)
while True:
    try:
        c.connect('192.168.1.5', 1883, 60)
        break
    except Exception as e:
        print('connect retry:', e, flush=True)
        time.sleep(2)
log(f"=== {time.strftime('%H:%M:%S')} 日志器v2启动（带自动重连）===")
c.loop_forever()
