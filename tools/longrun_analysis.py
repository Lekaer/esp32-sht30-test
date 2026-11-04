import csv, statistics, sys, time

CSV = '/Users/kaka/IOT/longrun/longrun_data.csv'
rows = list(csv.DictReader(open(CSV)))
if not rows:
    print('无数据'); sys.exit(1)

# 按 seq 重启分段（seq 回落=设备重启，分段统计）
segments, cur = [], [rows[0]]
for r in rows[1:]:
    if int(r['seq']) <= int(cur[-1]['seq']):
        segments.append(cur); cur = [r]
    else:
        cur.append(r)
segments.append(cur)

total_recv = len(rows)
total_dup = sum(int(r['dup']) for r in rows)
total_gap_events = sum(1 for r in rows if float(r['gap_s'] or 0) > 6.5)
big_gaps = [(r['ts'], r['gap_s']) for r in rows if float(r['gap_s'] or 0) > 6.5]
heaps = [int(r['heap']) for r in rows if r['heap']]

def hhmm(s):
    t = int(s); return f'{t//3600}h{(t%3600)//60}m'

print('## 7x24 长测统计分析\n')
print(f'| 指标 | 结果 |')
print(f'|---|---|')
print(f'| 数据文件 | {CSV} |')
print(f'| 记录总数 | {total_recv} 条 |')
print(f'| 设备重启分段 | {len(segments)} 段 |')
for i, seg in enumerate(segments):
    dur = (len(seg) - 1) * 2
    exp = dur / 2 + 1
    lost = int(seg[-1]['seq']) - int(seg[0]['seq']) + 1 - len(seg)
    print(f'| 第 {i+1} 段（{seg[0]["ts"]} 起） | 运行 {hhmm(dur)}，应收 {int(exp)} 实收 {len(seg)}，丢 {max(lost,0)} |')
print(f'| 重复消息 | {total_dup} 条 |')
print(f'| 缺口事件(>6.5s) | {total_gap_events} 次 |')
for ts, g in big_gaps[:10]:
    print(f'| 缺口 | {ts} 间隔 {g}s |')
if heaps:
    print(f'| heap 首/末 | {heaps[0]} → {heaps[-1]} 字节 |')
    print(f'| heap 最小/最大 | {min(heaps)} / {max(heaps)} |')
    drift = heaps[-1] - heaps[0]
    print(f'| heap 漂移 | {drift:+d} 字节（持续下降=疑似内存泄漏） |')
recv_seqs = sum(int(seg[-1]['seq']) - int(seg[0]['seq']) + 1 for seg in segments)
avail = total_recv / recv_seqs * 100 if recv_seqs else 0
print(f'| 消息到达率 | {avail:.2f}% |')
