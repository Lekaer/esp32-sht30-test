# ESP32-S3 IoT 测试链路（SHT30 → MQTT）

独立搭建的 IoT 设备测试项目：**不止于"让传感器上云"，重点是对整条链路做系统的质量验证**——测试点设计、可控故障注入、缺陷定位、消费端自动化断言、结构化测试报告。

## 架构

```
SHT30 ──I2C──> ESP32-S3 ──Wi-Fi(2.4G)──> MQTT broker ──> Python 校验端
 (0x44)       (seq 序号报文)           (本地 mosquitto     (五层断言:
                                         作可控测试替身)     格式/结构/量程/
                                                            seq 连续/频率)
```

## 核心产出

- **10 条弱网/断连重连测试点**（T1-T10）全执行：broker 宕机/恢复、断网/恢复、弱信号覆盖边缘、消息丢失、重复乱序、长时间稳定性、设备重启、故障发现速度
- **Defect #1（真实缺陷）**：网络恢复初期连接抖动——首次重连约 12s 后掉线、二次重连才稳定（间歇性，有日志双缺口铁证）；改进方向=连接健康检查/指数退避
- **自动化断言统计**：断网丢消息 25 条（seq 229→255 精确统计）、恢复后重复 0 条、基线间隔 2.02s±0.3s
- 📄 [设备测试报告](docs/ESP32设备测试报告.md)（测试点/环境/结果/缺陷/自动化校验/过程教训）
- 📄 [实操手册](docs/ESP32实操手册.md)（S3 四手感/串口三板斧/面包板三大暗规则/五连排查案例）

## 目录

```
firmware/sht30_mqtt/   设备固件：MQTT 上报版（seq 序号，弱网测试对象）
firmware/sht30_oled/   温湿度计原型：SHT30+OLED 共享 I2C 总线，含异常路径
tools/                 mqtt_logger.py（带时间戳日志器）/ mqtt_validator.py（五层断言校验端）
docs/                  测试报告 / 实操手册 / 接线图
data/                  自动化校验原始结果
```

## 复现要点

1. 本地 broker：`brew install mosquitto`，配置 `listener 1883 0.0.0.0` + `allow_anonymous true`，固件里 BROKER 改本机局域网 IP
2. 固件烧录需手动进下载模式：按住 BOOT → 上传 → 见 Connecting 松开；`Hard resetting via RTS` 挂起=成功，手动按 RST
3. Tools → USB CDC On Boot 必须 Enabled，否则串口无输出
4. 校验端：`python3 mqtt_validator.py 300`（窗口秒数），结果追加至 data/validation_result.md

## 测试关键词

弱网测试 / 断连重连 / 故障注入（fault injection）/ 覆盖边缘 flapping / 消息完整性（seq 连续性=资金流水号对账同构）/ QoS 语义分析 / 观测链路可靠性 / 测试替身（本地 broker）/ 消费端契约断言

## 后续方向

- Defect#1 修复（指数退避/健康检查）+ 回归验证
- QoS1 + 消费端幂等去重改造
- 断连期间本地缓存/补发机制
- CAN（TWAI）收发 demo——扩展车规词汇
