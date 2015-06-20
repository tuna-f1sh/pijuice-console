import uinput, time, math
import RPi.GPIO as GPIO
from Adafruit_ADS1x15 import ADS1x15

# ---- OPTIONS ----
#===================

# BCM GPIO PIN : ASCII KEYBOARD MAPPING (25 used by PiTFT)
# You can change the BCM GPIO map and corresponding key press event here
buttons = {
        17 : uinput.KEY_Z,
        27 : uinput.KEY_Q,
        23 : uinput.KEY_LEFTCTRL,
        24 : uinput.KEY_SPACE,
        18 : uinput.BTN_JOYSTICK
        }

# Joystick AXIS mapping to ADC channels
Y_AXIS = 1
X_AXIS = 0

# Hardware settings
ADS1015 = 0x00  # 12-bit ADC
DZONE = 500 # dead zone applied to joystick (mV)
VREF = 3300 # joystick Vcc (mV)

# ---- OPTIONS END ----
#=======================

state = {x : 0 for x in buttons} # button internal state

# Initialise the ADC using the default mode (use default I2C address)
adc = ADS1x15(ic=ADS1015)
gain = 4096
sps = 250

# Initialise the joystick events, mapped between the voltage readings of the ADC:
# 0 - Down/Right : VREF/2 - Center : VREF - Up/Left
events = [uinput.ABS_X + (0, VREF, 0, 0), uinput.ABS_Y + (0, VREF, 0, 0)]

# Initialise GPIO and button events
GPIO.setmode(GPIO.BCM)
for x in buttons:
    GPIO.setup(x, GPIO.IN, pull_up_down=GPIO.PUD_UP) # pull-up so button connects to ground
    # append buttons used to uinput events
    events.append(buttons[x])

# Setup HID emulator
device = uinput.Device(events)
time.sleep(1)

# center sticks
device.emit(uinput.ABS_X, VREF/2, syn=False);
device.emit(uinput.ABS_Y, VREF/2);

# Function to read data from I2C chip using Adafruit lib
# Channel must be an integer 0-3
def ReadChannel(channel):
    data = adc.readADCSingleEnded(channel, gain, sps)
    #print data
    return data

# Maps ADC reading to Joystick position
def digitalJoy(axis):
    value = int(ReadChannel(axis))
    # If the stick moved in a direction outside the deadzone
    if (value > (VREF/2 + DZONE)) or (value < (VREF/2 - DZONE)):
        if axis == X_AXIS:
            device.emit(uinput.ABS_X, int(math.floor(value)))
        else:
            device.emit(uinput.ABS_Y, int(math.floor(value)))
    # center the sticks
    else: 
        if axis == X_AXIS:
            device.emit(uinput.ABS_X, VREF/2)
        else:
            device.emit(uinput.ABS_Y, VREF/2)

# Read and sets state of GPIO buttons
def setState(state, button, key):
    if (not state) and (not GPIO.input(button)):
        state = True
        device.emit(key, 1)
        # print key
        # print button
    if state and GPIO.input(button):
        state = False
        device.emit(key, 0)
    return state

# The loop polls GPIO and joystick state every 20ms
while True:
    # check button states
    for button in buttons:
        key = buttons[button]
        state[button] = setState(state[button],button,key)
    # check joystick states
    digitalJoy(Y_AXIS)
    digitalJoy(X_AXIS)

    time.sleep(.02)
