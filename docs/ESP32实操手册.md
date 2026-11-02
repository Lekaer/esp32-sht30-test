# ESP32-S3 实操手册（W1 项目期操作手册 v1）

> 配套：lessons/0019-esp32-lab.html（五步路线）、/Users/kaka/IOT/wiring_guide.png（接线图）
> 记录至 2026-11-02（Day2 完成：SHT30 I2C 打通 0x44）。过程案例见 NOTES.md 2026-11-01/11-02 条目。

## 一、环境（已完成，重装时参考）

- 手动安装路径（官方 Boards Manager 会被 GitHub 限流到 ~25KB/s，不可用）：
  1. 核心：GitCode 镜像 `git clone --depth 1 --branch 3.3.12 https://gitcode.com/gh_mirrors/ar/arduino-esp32.git` → `~/Library/Arduino15/packages/esp32/hardware/esp32/3.3.12`（GitHub 代理 ghproxy/gh-proxy 均会断流；码云无镜像）
  2. 工具链：aria2 多线程（`-x16 -s16`，25MB/s，比单线程快 1000 倍）从 package_esp32_index.template.json 提取的 URL 下载 7 个文件（共 1.7GB）到 `tools/dist/`，sha256 全过后 `python3 tools/get.py` 本地解压
  3. IDE 里直接选 ESP32S3 Dev Module 即可，Boards Manager 那个安装不用管
- 本机关键路径：核心 `~/Library/Arduino15/packages/esp32/hardware/esp32/3.3.12`，工具 `同目录/tools/`

## 二、S3 板子操作四手感（每次上手必用）

1. **进下载模式**：按住 BOOT → 点上传 → 输出见 `Connecting` 时松开 BOOT
2. **烧写成功的标志**：输出停在 `Hard resetting via RTS pin...` 挂起 = 已成功（原生 USB 无 RTS 线），手动按 RST 运行
3. **复位后端口名会变**：`/dev/cu.usbmodemXXXX` 数字会变，IDE 里 Tools → Port 重选；列表空了就把 USB 拔掉重插
4. **USB CDC On Boot 必须 Enabled**（Tools 菜单）：否则 `Serial.print` 走 UART 不走 USB，串口一片空白。常开

## 三、串口观测三板斧（按顺序排查）

1. IDE 监视器 "Not connected" 但系统有端口 → 有进程占用：`lsof /dev/cu.usbmodem*` 找到后杀掉（见过 IDE 的 serial-monitor 卡死占口）
2. 端口能开但无数据 → 查 CDC 开关（上节第 4 条）
3. 按 RST 丢数据 → 复位时 USB 重新枚举、端口瞬断，且程序只在 setup 打印一次就会错过。对策：程序在 loop 里循环打印；或给板子加 RGB 自检灯（`rgbLedWrite(48, r, g, b)`：红=失败绿=通过），用灯态当判据绕开串口时序

## 四、面包板三大暗规则（血泪版）

1. **列内导通**：同字母列（a-e 五个孔）是一根导线，不同行之间连通
2. **行内导通**：同一字母行横向所有孔导通——**横躺在字母行上跨列的线 = 把途经的列全部短接**，禁止
3. **凹槽断路**：中央凹槽把每一列切成互不相通的两半——**同列俯视对齐但分居凹槽两侧 = 没连上**（Day2 压轴坑，耗时最长）

接线铁律：
- 跳线两端各自插孔：一端在【元件那根针的列】，另一端在【目标排针的列】，行不挑（同列即通）
- 检查法：**正上方俯视，对面包板边缘刻度**，跳线与目标排针垂直对齐才算对列，不凭手感
- 只用 3V3（3.3V），别碰 5V；开发板骑凹槽，模块各针独占一列
- 开发板引脚地图（下排从左到右）：`3V3 3V3 RST 4 5 6 7 15 16 17 18 8 3 46 9 10 ... 5V G`；上排最左 = GND

## 五、排查方法论（五连案例，写报告用）

Day2 真实链条，按序套用：
1. 观测通道问题（端口占用 lsof）→ 2. 观测通道配置（CDC）→ 3. 观测时序（循环打印/RGB 灯）→ 4. 接线逻辑（行导通短接）→ 5. 物理拓扑（凹槽断路）
- **加压测试**：按住模块下压同时复位，判断接触不良
- **对调测试**：互换疑似对调的两根线，判断顺序读反
- **最小改动原则**：每次只改一处，改完即测
- 口诀：先怀疑观测手段，再怀疑被测系统（这次前三个坑全在观测侧，被测系统最后才轮到）

## 六、SHT30 关键参数

- I2C 地址 0x44（部分 0x45），测量命令 0x2C06，等 20ms 读 6 字节
- 温度 = -45 + 175 × (ST/65535)，湿度 = 100 × (SRH/65535)
- 供电 2.4V-5.5V，但 S3 逻辑 3.3V，VCC 接 3V3

## 七、测试点记录（Day2 验收）

1. ✅ 上电串口每 2s 输出温湿度（循环打印版 sketch）
2. ✅ 捂手升温 / 哈气升湿（传感器响应验证）
3. 拔 SDA 报错——待测（Day3 后补）
