import smbus
import time
import calendar
import firebasedw
import urllib2
import json

url = "https://iotnoob.firebaseio.com"

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
#handle negative temps
if temp > 0x7FF:
	temp = temp-4096;
temp_C = float(temp) * 0.0625
temp_F = temp_C * 9/5+32

def readTemp():
  if temp > 0x7FF:
    temp = temp-4096;
  temp_C = float(temp) * 0.0625
  temp_F = temp_C * 9/5+32

def convertToNumber(data):
  # Simple function to convert 2 bytes of data
  # into a decimal number
  return ((data[1] + (256 * data[0])) / 1.2)

def readLight(addr=DEVICE):
  data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
  return convertToNumber(data)

def main():

  while True:
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
    print str(calendar.timegm(time.gmtime()))
    
    #fb.put('/','newage',50)
    fb.put('/','lightlevel',lightLevel)
    fb.put('/','temperature',"Temp = %3.1f C -- %3.1f F" % (temp_C,temp_F))
    fb.put('/','date',str(calendar.timegm(time.gmtime())))

    time.sleep(0.5)
  
if __name__=="__main__":
   main()
