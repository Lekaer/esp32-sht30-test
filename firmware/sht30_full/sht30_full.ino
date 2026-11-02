// ESP32-S3 产品完全体 v2.0：SHT30 采集 → OLED 显示 + MQTT 上报（seq+heap）
// I2C 总线共享：SHT30(0x44) + OLED(0x3C)，SDA=8 SCL=9
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <U8g2lib.h>

const char* SSID = "YOUR_WIFI_SSID";      // 2.4GHz
const char* PASS = "YOUR_WIFI_PASSWORD";
const char* BROKER = "192.168.1.5";
const uint16_t PORT = 1883;
const char* TOPIC  = "esp32/sht30-kaka";

uint32_t seq = 0;
WiFiClient espClient;
PubSubClient client(espClient);
U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);

bool readSHT30(float &t, float &h) {
  Wire.beginTransmission(0x44);
  Wire.write(0x2C);
  Wire.write(0x06);
  if (Wire.endTransmission() != 0) return false;
  delay(20);
  Wire.requestFrom(0x44, 6);
  if (Wire.available() < 6) return false;
  uint8_t buf[6];
  for (int i = 0; i < 6; i++) buf[i] = Wire.read();
  t = -45.0 + 175.0 * ((buf[0] << 8 | buf[1]) / 65535.0);
  h = 100.0 * ((buf[3] << 8 | buf[4]) / 65535.0);
  return true;
}

void showOLED(bool ok, float t, float h) {
  oled.clearBuffer();
  oled.setFont(u8g2_font_ncenB14_tf);
  if (ok) {
    oled.setCursor(0, 22);
    oled.print("Temp: "); oled.print(t, 1); oled.print(" C");
    oled.setCursor(0, 48);
    oled.print("Humi: "); oled.print(h, 1); oled.print(" %");
  } else {
    oled.setCursor(0, 30);
    oled.print("Sensor offline!");
  }
  oled.setFont(u8g2_font_6x13_tf);
  oled.setCursor(0, 62);
  oled.print(client.connected() ? "MQTT:OK seq=" : "MQTT:X seq=");
  oled.print(seq);
  oled.sendBuffer();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(8, 9);
  oled.begin();
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
      delay(2000);
    }
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  float t, h;
  bool ok = readSHT30(t, h);
  if (ok) {
    seq++;
    char payload[80];
    snprintf(payload, sizeof(payload), "{\"seq\":%u,\"temp\":%.1f,\"humi\":%.1f,\"heap\":%u}",
             seq, t, h, ESP.getFreeHeap());
    client.publish(TOPIC, payload);
    Serial.println(payload);
  } else {
    Serial.println("SHT30 离线");
  }
  showOLED(ok, t, h);
  delay(2000);
}
