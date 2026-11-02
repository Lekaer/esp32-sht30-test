// ESP32-S3 + SHT30 + OLED 温湿度计原型（消费级产品形态）
// SHT30 与 OLED 共享 I2C 总线（SDA=8, SCL=9，地址 0x44 / 0x3C）
// 异常路径：传感器离线时屏幕显示 "Sensor offline" 而非卡死
#include <Wire.h>
#include <U8g2lib.h>

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

void setup() {
  Serial.begin(115200);
  Wire.begin(8, 9);
  oled.begin();
}

void loop() {
  float t, h;
  oled.clearBuffer();
  oled.setFont(u8g2_font_ncenB14_tf);
  if (readSHT30(t, h)) {
    oled.setCursor(0, 22);
    oled.print("Temp: "); oled.print(t, 1); oled.print(" C");
    oled.setCursor(0, 48);
    oled.print("Humi: "); oled.print(h, 1); oled.print(" %");
  } else {
    oled.setCursor(0, 30);
    oled.print("Sensor offline!");
    oled.setCursor(0, 50);
    oled.print("check I2C wiring");
  }
  oled.sendBuffer();
  delay(2000);
}
