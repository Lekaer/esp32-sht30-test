import paho.mqtt.client as mqtt
import time, json, csv, os, sys

CSV = '/Users/kaka/IOT/longrun/longrun_data.csv'
os.makedirs(os.path.dirname(CSV), exist_ok=True)

new_file = not os.path.exists(CSV) or os.path.getsize(CSV) == 0
f = open(CSV, 'a', buffering=1)
w = csv.writer(f)
if new_file:
    w.writerow(['ts', 'seq', 'temp', 'humi', 'heap', 'gap_s', 'dup'])

state = {'last_seq': None, 'last_ts': None, 'count': 0,
         'dups': 0, 'gaps': 0, 'hour_start': time.time(), 'hour_count': 0}

def on_connect(c, u, flags, rc):
    c.subscribe('esp32/sht30-kaka')
    print(f"[{time.strftime('%H:%M:%S')}] 长测监视端上线/重连", flush=True)

def on_message(c, u, msg):
    now = time.time()
    try:
        d = json.loads(msg.payload.decode())
    except Exception:
        return
    gap = round(now - state['last_ts'], 2) if state['last_ts'] else 0
    dup = 0
    if state['last_seq'] is not None:
        if d['seq'] == state['last_seq']:
            dup = 1
            state['dups'] += 1
        elif d['seq'] > state['last_seq'] + 1:
            state['gaps'] += 1
    state['last_seq'] = d['seq']
    state['last_ts'] = now
    state['count'] += 1
    state['hour_count'] += 1
    w.writerow([time.strftime('%H:%M:%S'), d['seq'], d['temp'], d['humi'],
                d.get('heap', ''), gap, dup])
    if now - state['hour_start'] >= 3600:
        print(f"[{time.strftime('%H:%M:%S')}] 小时报：累计 {state['count']} 条 | "
              f"本小时 {state['hour_count']} 条 | 断档 {state['gaps']} | 重复 {state['dups']} | "
              f"heap {d.get('heap','?')}", flush=True)
        state['hour_start'] = now
        state['hour_count'] = 0

c = mqtt.Client()
c.on_connect = on_connect
c.on_message = on_message
c.reconnect_delay_set(min_delay=1, max_delay=10)
while True:
    try:
        c.connect('192.168.1.5', 1883, 60)
        break
    except Exception as e:
        print('connect retry:', e, flush=True)
        time.sleep(2)
print(f"[{time.strftime('%H:%M:%S')}] 长测监视启动，数据 -> {CSV}", flush=True)
c.loop_forever()
