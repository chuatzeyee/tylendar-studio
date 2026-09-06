# Hardware assembly

How to wire the panel, set the two switches that matter, and mount
everything in the IKEA RODALM frame. Read the handling notes first,
the panel is a sheet of glass.

## Handling the panel

- Hold the GDEM102F91 by its edges. Never press on the face and never
  rest it face down on a hard surface.
- The FPC ribbon tolerates gentle curves. Do not crease it to a sharp
  fold and do not fold it at the point where it leaves the glass.
- Never plug or unplug the ribbon while the board is powered. Power
  off (P2 switch) or unplug USB first. Hot plugging kills panels.

## Parts check

- GDEM102F91 panel with its FPC ribbon (FPC-7705)
- DESPI-C02 adapter board (small board with the ribbon connector,
  a RESE switch, and a double row socket)
- ESP32-L board (USB-C connector, CH340 chip, P2 switch, P3 jumper)
- IKEA RODALM 21x30 cm frame with its mat
- USB-C cable and any 5V USB power source

Note on power: the ESP32-L has no battery connector and no charging
circuit. It is powered from the USB-C port only. Plan for the cable to
reach a wall adapter behind or below the frame.

## Step 1: Set the switches before connecting anything

1. On the DESPI-C02 adapter, set the RESE switch to 2.2. This selects
   the current sense resistor for the booster. The GDEM102F91 requires
   2.2; the 0.47 position is for smaller panels and will not drive
   this one correctly.
2. On the ESP32-L board, make sure the P3 jumper is shorted (the small
   two pin header with a jumper cap). It is in series with the panel
   supply for current measurements; with the cap removed the panel
   gets no power at all.
3. Find the P2 switch on the ESP32-L. This is the panel power switch.
   Leave it off until everything is connected.

## Step 2: Connect the ribbon to the adapter

1. On the DESPI-C02 ribbon connector, flip the dark locking bar up
   (it hinges, do not pull it off).
2. Slide the panel ribbon in straight and fully, with the gold
   contacts facing up toward the locking bar. The printed side of the
   ribbon end faces down.
3. Flip the locking bar back down. Give the ribbon the gentlest tug to
   confirm it is seated. A half seated ribbon is the number one cause
   of a blank or streaked screen.

## Step 3: Mate the adapter to the ESP32-L

Seat the DESPI-C02 onto the double row header of the ESP32-L. The
boards are keyed by the connector position and only align one way; the
adapter sits over the board, not hanging off the side. Press evenly
until fully seated.

## Step 4: First power on

1. Flash the firmware first if you have not (see FLASHING_MACOS.md).
2. Connect USB-C, then switch P2 on.
3. Press the EN button. Within about 30 seconds the panel should start
   its refresh: a series of full screen flashes for roughly 20
   seconds, then the calendar appears.
4. If the screen stays blank: check P2 is on, P3 is capped, RESE is on
   2.2, and reseat the ribbon (power off first).

Let it run one full cycle and check the serial monitor if anything
looks wrong. Only frame it after a good refresh.

## Step 5: Cut the mat

The RODALM 21x30 mat ships with a 120x170 mm opening. The visible
active area of the panel is larger, so the opening must be enlarged to
142x214 mm, still centered:

- Widen by 22 mm total: remove 11 mm from the left edge and 11 mm from
  the right edge of the opening.
- Lengthen by 44 mm total: remove 22 mm from the top edge and 22 mm
  from the bottom edge.

Mark the new opening on the back of the mat with a pencil and ruler,
then cut with a fresh blade against a metal straightedge, several light
passes rather than one deep one. A 45 degree bevel looks nicest but a
clean vertical cut is fine at viewing distance.

The calendar renders in portrait, so the frame hangs in portrait with
the 214 mm dimension vertical.

## Step 6: Mount in the frame

1. Clean the frame glass on both sides. Dust behind glass is forever.
2. Lay the mat face down, then the panel face down onto it, centered
   in the opening. Check the centering from the front before fixing.
3. Fix the panel to the back of the mat along its edges with acid free
   tape (framers tape or Kapton). Tape the bezel edges only, never
   across the back of the active area.
4. Route the ribbon toward the frame back with one loose curve. Mount
   the ESP32-L and adapter stack to the frame backing board with
   adhesive standoffs or thick foam tape, positioned so the ribbon
   stays relaxed.
5. Cut a small notch in the frame backing for the USB-C cable, or exit
   it through the bottom edge if the back panel leaves a gap.
6. Close the frame. Power up, press EN once, and hang it.

## Daily operation

The board wakes at 00:20, 07:30, 13:00, and 19:00 Singapore time, pulls
the fresh image, spends about 20 seconds refreshing, and sleeps until
the next wake. The 19:00 refresh switches to the dark page (black on
weekdays, red on weekends); midnight switches back to light. If WiFi or the download fails it keeps the previous image
visible and retries hourly. No buttons, no maintenance. If the frame
moves somewhere new, add that network to the WIFI_NETWORKS list in
`config.h` and reflash once.

Four color e-paper prefers moderate temperatures and no direct sun.
Direct sunlight fades the film over time and heat slows refreshes, so
an interior wall is ideal.
