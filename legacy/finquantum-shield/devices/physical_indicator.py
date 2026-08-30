"""
Physical quantum link status indicator.
Uses a USB-controlled RGB LED (or serial/Arduino) to show real-time
quantum channel health.

Hardware: Any USB RGB LED or Arduino Nano with WS2812B LED.
Cost: ₹200-500 ($2-6)
Impact: MASSIVE for in-person demos.
"""

import httpx
import time

# Try to import USB LED library (optional — gracefully degrades)
try:
    import usb.core  # pyusb for USB LED control

    HAS_USB = True
except ImportError:
    HAS_USB = False

# Try Arduino serial
try:
    import serial

    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class PhysicalIndicator:
    COLORS = {
        "GREEN": (0, 255, 0),
        "YELLOW": (255, 200, 0),
        "RED": (255, 0, 0),
    }

    def __init__(self, kms_url="http://localhost:8000"):
        self.kms_url = kms_url
        self.connected = False

        if HAS_SERIAL:
            try:
                self.arduino = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
                self.connected = True
                print("[LED] Arduino connected")
            except:
                pass

    def update(self):
        """Poll KMS and update LED color."""
        try:
            r = httpx.get(f"{self.kms_url}/link_status", timeout=2)
            status = r.json().get("status", "RED")
            r_c, g_c, b_c = self.COLORS.get(status, (255, 0, 0))
            self._set_color(r_c, g_c, b_c)
        except:
            self._set_color(255, 0, 0)  # Red on error

    def _set_color(self, r, g, b):
        if HAS_SERIAL and self.connected:
            self.arduino.write(f"{r},{g},{b}\\n".encode())

    def run_loop(self, interval=1):
        """Continuously update LED."""
        while True:
            self.update()
            time.sleep(interval)


if __name__ == "__main__":
    indicator = PhysicalIndicator()
    print("Starting Physical Indicator polling...")
    indicator.run_loop()
