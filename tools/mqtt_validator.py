import paho.mqtt.client as mqtt
import time, json, statistics, sys

BROKER = '192.168.1.5'
TOPIC = 'esp32/sht30-kaka'
DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 300   # 校验窗口秒数，默认 5 分钟
OUT = '/Users/kaka/IOT/validation_result.md'

stats = {
    'total': 0, 'parse_err': 0, 'schema_err': 0, 'range_err': 0,
    'intervals': [], 'seq_gaps': [], 'seq_dups': 0, 'first_seq': None, 'last_seq': None,
    'last_ts': None, 'last_seq_val': None,
}
errors = []

def on_connect(c, u, f, rc):
    c.subscribe(TOPIC)
    print(f'[校验端已订阅 {TOPIC}，窗口 {DURATION}s]', flush=True)

def on_message(c, u, msg):
    now = time.time()
    raw = msg.payload.decode()
    stats['total'] += 1

    # 1. JSON 可解析性
    try:
        d = json.loads(raw)
    except Exception:
        stats['parse_err'] += 1
        errors.append(f'JSON 解析失败: {raw}')
        return

    # 2. 结构断言
    if not isinstance(d.get('seq'), int) or not isinstance(d.get('temp'), (int, float)) or not isinstance(d.get('humi'), (int, float)):
        stats['schema_err'] += 1
        errors.append(f'结构错误: {raw}')
        return

    # 3. 范围断言（SHT30 物理量程）
    if not (-40 <= d['temp'] <= 85) or not (0 <= d['humi'] <= 100):
        stats['range_err'] += 1
        errors.append(f'超量程: {raw}')

    # 4. 序列连续性（丢消息/重复消息）
    if stats['last_seq_val'] is not None:
        diff = d['seq'] - stats['last_seq_val']
        if diff > 1:
            stats['seq_gaps'].append((stats['last_seq_val'], d['seq'], diff - 1))
        elif diff == 0:
            stats['seq_dups'] += 1
            errors.append(f'序列号重复: seq={d["seq"]}')
    else:
        stats['first_seq'] = d['seq']
    stats['last_seq_val'] = d['seq']

    # 5. 频率统计
    if stats['last_ts'] is not None:
        stats['intervals'].append(now - stats['last_ts'])
    stats['last_ts'] = now

c = mqtt.Client()
c.on_connect = on_connect
c.on_message = on_message
c.connect(BROKER, 1883, 60)
c.loop_start()
time.sleep(DURATION)
c.loop_stop()

# 汇总
s = stats
lost = sum(g[2] for g in s['seq_gaps'])
iv = s['intervals']
report = []
report.append(f'\n## 校验结果（窗口 {DURATION}s，{time.strftime("%H:%M")}）\n')
report.append(f'| 指标 | 结果 | 判定 |')
report.append(f'|---|---|---|')
report.append(f'| 接收消息总数 | {s["total"]} | |')
report.append(f'| JSON 解析失败 | {s["parse_err"]} | {"✅" if s["parse_err"]==0 else "❌"} |')
report.append(f'| 结构断言失败 | {s["schema_err"]} | {"✅" if s["schema_err"]==0 else "❌"} |')
report.append(f'| 范围断言失败 | {s["range_err"]} | {"✅" if s["range_err"]==0 else "❌"} |')
report.append(f'| 丢失消息（seq 断档） | {lost} 条，断档 {len(s["seq_gaps"])} 处 | |')
report.append(f'| 重复消息（seq 重复） | {s["seq_dups"]} 条 | {"✅" if s["seq_dups"]==0 else "❌"} |')
if iv:
    report.append(f'| 消息间隔 | 均值 {statistics.mean(iv):.2f}s / 最大 {max(iv):.1f}s / 最小 {min(iv):.2f}s | 期望≈2s |')
report.append('')
if s['seq_gaps']:
    report.append('**丢消息明细**：')
    for a, b, n in s['seq_gaps']:
        report.append(f'- seq {a} → {b}，丢 {n} 条')
if errors:
    report.append(f'\n**异常样本**（前 10 条）：')
    for e in errors[:10]:
        report.append(f'- {e}')

text = '\n'.join(report)
with open(OUT, 'a') as f:
    f.write(text + '\n')
print(text)
print(f'\n已追加写入 {OUT}')
