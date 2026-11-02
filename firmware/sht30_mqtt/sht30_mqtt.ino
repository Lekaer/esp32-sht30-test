// ESP32-S3 + SHT30 → MQTT 上报（测试项目固件）
// 链路：SHT30 --I2C--> ESP32-S3 --WiFi--> MQTT broker
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>

const char* SSID = "YOUR_WIFI_SSID";      // 2.4GHz only
const char* PASS = "YOUR_WIFI_PASSWORD";
const char* BROKER = "192.168.1.5";       // 本地 mosquitto；公共 broker 可用 broker.emqx.io
const uint16_t PORT = 1883;
const char* TOPIC  = "esp32/sht30-kaka";

uint32_t seq = 0;                          // 消息序号：消费端断言丢消息/重复的关键
WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  Wire.begin(8, 9);                        // SDA=GPIO8, SCL=GPIO9
  delay(1000);

  WiFi.begin(SSID, PASS);
  Serial.print("连接 Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println(" 已连接！IP: " + WiFi.localIP().toString());

  client.setServer(BROKER, PORT);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("连接 MQTT...");
    if (client.connect("esp32s3-kaka-001")) {
      Serial.println("已连接！");
    } else {
      Serial.print("失败，重试 ");
      delay(2000);                          // 固定退避——Defect#1 改进点（指数退避/健康检查）
    }
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  Wire.beginTransmission(0x44);            // SHT30 测量命令 0x2C06
  Wire.write(0x2C);
  Wire.write(0x06);
  Wire.endTransmission();
  delay(20);
  uint8_t buf[6];
  Wire.requestFrom(0x44, 6);
  for (int i = 0; i < 6; i++) buf[i] = Wire.read();

  float temp = -45.0 + 175.0 * ((buf[0] << 8 | buf[1]) / 65535.0);
  float humi = 100.0 * ((buf[3] << 8 | buf[4]) / 65535.0);

  seq++;
  char payload[64];
  snprintf(payload, sizeof(payload), "{\"seq\":%u,\"temp\":%.1f,\"humi\":%.1f,\"heap\":%u}", seq, temp, humi, ESP.getFreeHeap());
  client.publish(TOPIC, payload);          // QoS0：至多一次，断网无补偿（见测试报告）
  Serial.println(payload);
  delay(2000);
}
