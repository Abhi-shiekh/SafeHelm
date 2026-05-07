#include <soc/rtc_cntl_reg.h>
#include <Wire.h>

#define IR_PIN           34
#define MPU_ADDR         0x68
#define IMPACT_THRESHOLD 2.5
#define HELMET_THRESHOLD 2000
#define IMPACT_COOLDOWN  2000

bool impact_detected = false;
unsigned long last_impact_time = 0;

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);
  Wire.begin(21, 22);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
}

float readAccel() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6, true);
  int16_t ax = Wire.read() << 8 | Wire.read();
  int16_t ay = Wire.read() << 8 | Wire.read();
  int16_t az = Wire.read() << 8 | Wire.read();
  return sqrt(pow(ax / 16384.0, 2) + pow(ay / 16384.0, 2) + pow(az / 16384.0, 2));
}

void loop() {
  int ir = analogRead(IR_PIN);
  bool helmet_on = ir < HELMET_THRESHOLD;
  float accel = readAccel();

  unsigned long now = millis();
  if (impact_detected && now - last_impact_time >= IMPACT_COOLDOWN)
    impact_detected = false;
  if (!impact_detected && accel > IMPACT_THRESHOLD) {
    impact_detected = true;
    last_impact_time = now;
  }

  Serial.printf("{\"ir\":%d,\"accel\":%.2f,\"helmet_on\":%s,\"impact\":%s}\n",
    ir,
    accel,
    helmet_on      ? "true" : "false",
    impact_detected ? "true" : "false"
  );

  delay(100);
}