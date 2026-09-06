#pragma once

#include <Arduino.h>

// Minimal streaming driver for the Good Display GDEM102F91.
// 10.2 inch, 960x640, four colors (black, white, yellow, red),
// SSD2677 controller. Init values transcribed from the official
// Good Display sample code (AU-GDEM0102F91, 2024-02-01).
//
// Frame format: 2 bits per pixel, 4 pixels per byte MSB first,
// 00 black, 01 white, 10 yellow, 11 red, 960*640/4 = 153600 bytes.

#define EPD_WIDTH 960
#define EPD_HEIGHT 640
#define EPD_FRAME_BYTES (EPD_WIDTH * EPD_HEIGHT / 4L)

void epdPinsBegin();
bool epdInit();       // reset and power on, false on busy timeout
void epdStartFrame(); // send the data write command 0x10
void epdWriteData(const uint8_t *data, size_t len);
bool epdRefresh();    // trigger refresh, wait until done (about 20 s)
void epdPowerOffAndSleep();
