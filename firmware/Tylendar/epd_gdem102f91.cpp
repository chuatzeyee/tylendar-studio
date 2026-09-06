#include "epd_gdem102f91.h"
#include "config.h"
#include <SPI.h>

static const uint32_t SPI_HZ = 10000000;
static const uint32_t BUSY_INIT_TIMEOUT_MS = 5000;
static const uint32_t BUSY_REFRESH_TIMEOUT_MS = 45000;

// BUSY is active low: 0 while working, 1 when idle.
static bool waitIdle(uint32_t timeout_ms) {
  uint32_t start = millis();
  while (digitalRead(PIN_BUSY) == LOW) {
    if (millis() - start > timeout_ms) return false;
    delay(10);
  }
  return true;
}

static void writeCmd(uint8_t cmd) {
  SPI.beginTransaction(SPISettings(SPI_HZ, MSBFIRST, SPI_MODE0));
  digitalWrite(PIN_DC, LOW);
  digitalWrite(PIN_CS, LOW);
  SPI.transfer(cmd);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

static void writeData(uint8_t data) {
  SPI.beginTransaction(SPISettings(SPI_HZ, MSBFIRST, SPI_MODE0));
  digitalWrite(PIN_DC, HIGH);
  digitalWrite(PIN_CS, LOW);
  SPI.transfer(data);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

void epdPinsBegin() {
  pinMode(PIN_BUSY, INPUT);
  pinMode(PIN_RST, OUTPUT);
  pinMode(PIN_DC, OUTPUT);
  pinMode(PIN_CS, OUTPUT);
  digitalWrite(PIN_CS, HIGH);
  digitalWrite(PIN_RST, HIGH);
  SPI.begin();
}

bool epdInit() {
  delay(100);
  digitalWrite(PIN_RST, LOW);
  delay(10);
  digitalWrite(PIN_RST, HIGH);
  delay(10);
  if (!waitIdle(BUSY_INIT_TIMEOUT_MS)) return false;

  writeCmd(0x00); // panel setting
  writeData(0x2F);
  writeData(0x29);

  writeCmd(0x03); // power off sequence
  writeData(0x10);
  writeData(0x54);
  writeData(0x44);

  writeCmd(0x06); // booster soft start
  writeData(0x0F);
  writeData(0x8B);
  writeData(0x93);
  writeData(0xA1);

  writeCmd(0x41); // temperature sensor
  writeData(0x00);

  writeCmd(0x50); // VCOM and data interval
  writeData(0x37);

  writeCmd(0x60); // TCON
  writeData(0x02);
  writeData(0x02);

  writeCmd(0x61); // resolution
  writeData(EPD_WIDTH / 256);
  writeData(EPD_WIDTH % 256);
  writeData(EPD_HEIGHT / 256);
  writeData(EPD_HEIGHT % 256);

  writeCmd(0x65); // gate start setting
  writeData(0x00);
  writeData(0x00);
  writeData(0x00);
  writeData(0x00);

  writeCmd(0xE7);
  writeData(0x1C);

  writeCmd(0xE3);
  writeData(0x00);

  writeCmd(0xE9);
  writeData(0x01);

  writeCmd(0x30); // frame rate, matches the waveform
  writeData(0x08);

  writeCmd(0x62); // waveform tuning block from the factory sample
  writeData(0x7D);
  writeData(0x7D);
  writeData(0x7D);
  writeData(0x60);
  writeData(0xA7);
  writeData(0x93);
  writeData(0x7D);
  writeData(0x68);

  writeCmd(0x04); // power on
  return waitIdle(BUSY_INIT_TIMEOUT_MS);
}

void epdStartFrame() {
  writeCmd(0x10);
}

void epdWriteData(const uint8_t *data, size_t len) {
  SPI.beginTransaction(SPISettings(SPI_HZ, MSBFIRST, SPI_MODE0));
  digitalWrite(PIN_DC, HIGH);
  digitalWrite(PIN_CS, LOW);
  SPI.writeBytes(data, len);
  digitalWrite(PIN_CS, HIGH);
  SPI.endTransaction();
}

bool epdRefresh() {
  writeCmd(0x12);
  writeData(0x00);
  return waitIdle(BUSY_REFRESH_TIMEOUT_MS);
}

void epdPowerOffAndSleep() {
  writeCmd(0x02); // power off
  waitIdle(BUSY_INIT_TIMEOUT_MS);
  delay(100); // the factory sample marks this delay as mandatory
  writeCmd(0x07); // deep sleep
  writeData(0xA5);
}
