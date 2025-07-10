import RPi.GPIO as GPIO
import time
import argparse
import signal
import sys
import math

# Setup command-line arguments
parser = argparse.ArgumentParser(description="Play tone on speaker via GPIO.")
parser.add_argument('-f', '--frequency', type=int, default=50, help="Frequency of the tone in Hz")
parser.add_argument('-d', '--duration', type=float, default=0, help="Duration in seconds (0 for indefinite)")
parser.add_argument('-s', '--sweep', type=bool, default=False, help="Sweep through the frequencies")
args = parser.parse_args()

SPEAKER_PIN = 18

# Graceful exit handler
def signal_handler(sig, frame):
    print("\nStopping tone...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SPEAKER_PIN, GPIO.OUT)
pwm = GPIO.PWM(SPEAKER_PIN, args.frequency)

base = 100
freqs = [math.ceil(pow(2,1/12)**x*base) for x in range(1,25)]

try:
    pwm.start(50)
    i = 0
    while True:
        pwm.ChangeFrequency(freqs[i])
        time.sleep(0.25)
        i += 1
        if i == 25:
            i = 0
finally:
    if pwm is not None:
        try:
            pwm.stop()
            del pwm  # <-- Explicitly delete it before GPIO.cleanup()
        except Exception as e:
            print("Warning while stopping PWM:", e)
    GPIO.cleanup()
