#pragma once

// WiFi networks, tried in order at every wake, so the frame can move
// between home and work without reflashing. One {ssid, password} pair
// per line. 2.4GHz networks with an ordinary password only: corporate
// login networks (802.1X) and captive portals will not work.
//
// If none of these can be joined, the board opens its own access point
// "Tylendar" (password "tylendar") for 3 minutes with a setup page
// where a new network can be typed in from a phone. That network is
// saved to the board's flash and tried first at every wake, so the
// list below is just the starting set.
#define WIFI_NETWORKS \
  { \
    {"YOUR_HOME_SSID", "YOUR_HOME_PASSWORD"}, \
    {"YOUR_WORK_SSID", "YOUR_WORK_PASSWORD"}, \
  }

// Where the rendered image lives. GitHub Actions in this repo re-renders
// it 15 to 25 minutes before each wake time below.
#define IMAGE_URL "https://raw.githubusercontent.com/chuatzeyee/Tylendar/main/output/tylendar.bin"

// Timezone offset from UTC in seconds. Singapore is UTC+8.
#define TZ_OFFSET_SECONDS (8 * 3600)

// Local times of the daily refreshes as minutes after midnight, in
// ascending order: 00:20 (new day, back to light), 07:30 and 13:00
// (calendar events added during the morning), 19:00 (dark mode).
#define WAKE_TIMES {20, 7 * 60 + 30, 13 * 60, 19 * 60}

// How long to sleep before retrying after any failure, in minutes.
#define RETRY_MINUTES 60

// Pin mapping of the Good Display ESP32-L board to the DESPI-C02
// adapter. Taken from the official Good Display sample code for this
// kit: BUSY=A14, RES=A15, DC=A16, CS=A17. SPI uses the ESP32 default
// VSPI pins, SCK=18 and MOSI=23.
#define PIN_BUSY 13
#define PIN_RST 12
#define PIN_DC 14
#define PIN_CS 27
