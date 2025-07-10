import RPi.GPIO as GPIO
import time
import argparse
import signal
import sys


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

try:
    pwm.start(50)
    if args.sweep == False:
        print(f"Playing {args.frequency}Hz tone", end='')
        if args.duration == 0:
            print(" indefinitely. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        else:
            print(f" for {args.duration} seconds.")
            time.sleep(args.duration)
            pwm.stop()
    else:
        print(f"Sweeping through frequencies", end='')
        print(f"")
        step = 1
        delay = 0.1
        while True:
            for freq in range(1, args.frequency + 1, step):
                pwm.ChangeFrequency(freq)
                print(freq)
                time.sleep(delay)
            for freq in range(args.frequency, 0, -step):
                pwm.ChangeFrequency(freq)
                print(freq)
                time.sleep(delay)
finally:
    if pwm is not None:
        try:
            pwm.stop()
            del pwm  # <-- Explicitly delete it before GPIO.cleanup()
        except Exception as e:
            print("Warning while stopping PWM:", e)
    GPIO.cleanup()
