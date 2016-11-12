import smbus
import time
import calendar
import firebasedw
import urllib2
import json
import RPi.GPIO as GPIO                     # Uses the Pi's GPIO pins
#from SmartMCP3008 import SmartMCP3008       # Uses MCP3008 as ADC
import SoundDetector    # Sound Detector library
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

url = "https://iot-app-1ace2.firebaseio.com/"

fb = firebasedw.FirebaseApplication(url,None)

# Define some constants from the datasheet

DEVICE     = 0x23 # Default device I2C address

POWER_DOWN = 0x00 # No active state
POWER_ON   = 0x01 # Power on
RESET      = 0x07 # Reset data register value

# Start measurement at 4lx resolution. Time typically 16ms.
CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
# Device is automatically set to Power Down after measurement.
ONE_TIME_LOW_RES_MODE = 0x23

#bus = smbus.SMBus(0) # Rev 1 Pi uses 0
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

DEVICE_ADDRESS = 0x48      

#Read the temp register
temp_reg_12bit = bus.read_word_data(DEVICE_ADDRESS , 0 )
temp_low = (temp_reg_12bit & 0xff00) >> 8
temp_high = (temp_reg_12bit & 0x00ff)
#convert to temp from page 6 of datasheet
temp  = ((( temp_high * 256 ) + temp_low) >> 4 )

def read_audio():
        # Current GPIO Schematic
        audio = 0
        soundGate = 4                  # Connected to Pin 3, or SCL

        # Current MCP3008 Schematic
        soundAudio = 0                 # Connected to Pin 0 on MCP3008
        soundEnvelope = 1              # Connected to Pin 1 on MCP3008
        # Software SPI configuration:
        CLK  = 18
        MISO = 23
        MOSI = 24
        CS   = 25
        mcp3008 = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

        # Instantiate SoundDetector
        sound = SoundDetector.SoundDetector(soundGate, soundAudio, soundEnvelope)

        # Instantiate MCP3008
        #mcp3008 = SmartMCP3008.SmartMCP3008()

        # Setup RPi.GPIO to interpret GPIO as the Broadcom (BCM) pins
        GPIO.setmode(GPIO.BCM)

        # Setup GPIO as Input and Output for soundGate
        GPIO.setup(soundGate, GPIO.IN)
        if 1 == GPIO.input(sound.get_gate()):   # GPIO interprets value of Gate pin
          state = True
          status = 'HIGH'
        else:
          state = False
          status = 'LOW'
            # Print status of gate

            # Print value of audio interpreted by MCP3008 ADC
        audio = mcp3008.read_adc(sound.get_audio())
        return audio
#handle negative temps
if temp > 0x7FF:
  temp = temp-4096;
temp_C = float(temp) * 0.0625
temp_F = temp_C * 9/5+32

def readTemp():
  if temp > 0x7FF:
    temp = temp-4096
  temp_C = float(temp) * 0.0625
  temp_F = temp_C * 9/5+32

def convertToNumber(data):
  # Simple function to convert 2 bytes of data
  # into a decimal number
  return ((data[1] + (256 * data[0])) / 1.2)

def readLight(addr=DEVICE):
  data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
  return convertToNumber(data)

def OnSessionStarted():
  return (bool)(fb.get('/session'))

def main():
  #for i in range(10): #try running for 4 times first
    temp_reg_12bit = bus.read_word_data(DEVICE_ADDRESS , 0 )
    temp_low = (temp_reg_12bit & 0xff00) >> 8
    temp_high = (temp_reg_12bit & 0x00ff)
    #convert to temp from page 6 of datasheet
    temp  = ((( temp_high * 256 ) + temp_low) >> 4 )
    #handle negative temps
    if temp > 0x7FF:
            temp = temp-4096;
    temp_C = float(temp) * 0.0625
    temp_F = temp_C * 9/5+32
    lightLevel = str(readLight()) + " lx"
    print "Light Level : " + lightLevel
    print "Temp = %3.1f C -- %3.1f F" % (temp_C,temp_F)
    print "Audio level : " + str(read_audio())
    #print str(calendar.timegm(time.gmtime()))
    
    #fb.put('/','newage',50)
    # fb.put('/','light',readLight())
    # fb.put('/','temperature',"Temp = %3.1f C -- %3.1f F" % (temp_C,temp_F))
    # fb.put('/','temperature',temp_C)
    # fb.put('/','date',str(calendar.timegm(time.gmtime())))
    putDataIntoFirebase("light", readLight())
    putDataIntoFirebase("temperature", temp_C)
    putDataIntoFirebase("noise", read_audio())

    time.sleep(0.1)

def putDataIntoFirebase(device, data=None):
    current_timing = (int)(fb.get('/'+device+"/counter"))
    timing = current_timing+1
    fb.put('/' + device+ "/", str(timing), data)
    fb.put('/' + device, "/current", data)
    fb.put('/' + device, "/counter", timing)

if __name__=="__main__":
  print "Start session"
##  while OnSessionStarted():
  while True:
    main()
  print "Stop session"
