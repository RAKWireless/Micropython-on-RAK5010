#this file is the rui script of 5010, inlude bg96 and other sensors.
#use ampy --port /dev/ttyACM0 put rui.py to your board

import time
import math
from machine import Pin
from machine import UART
from machine import I2C


i2c=I2C(1,13,14)
uart=UART(0,115200)

def get_acceleration():
	x_l=i2c.readfrom_mem(0x19,0x28,1)
	x_h=i2c.readfrom_mem(0x19,0x29,1)
	y_l=i2c.readfrom_mem(0x19,0x2a,1)
	y_h=i2c.readfrom_mem(0x19,0x2b,1)
	z_l=i2c.readfrom_mem(0x19,0x2c,1)
	z_h=i2c.readfrom_mem(0x19,0x2d,1)
	x= (x_h[0]<<8) | x_l[0]
	y= (y_h[0]<<8) | y_l[0]
	z= (z_h[0]<<8) | z_l[0]

	if x < 0x8000:
		x=x
	else:
		x=x-0x10000
	if y < 0x8000:
		y=y
	else:
		y=y-0x10000

	if z < 0x8000:
		z=z
	else:
		z=z-0x10000

	acc_x=(x*4000)/65536.0
	acc_y=(y*4000)/65536.0
	acc_z=(z*4000)/65536.0
	print('lis3dh:acc_x=%f,acc_y=%f,acc_z=%f'%(acc_x,acc_y,acc_z))




def get_light_strength():
	buf=i2c.readfrom_mem(0x44,0x00,2)
	light=int.from_bytes(buf,'big')
	m=light & 0x0FFF
	e=(light & 0xF000) >> 12
	h= math.pow(2,e)
	light = m*(0.01 * h)
	print('opt3001:light strength = %f'%light)



def get_temperature_humidity():
	buf=bytearray([0x7C,0xA2])
	i2c.writeto(0x70,buf)
	buf2=bytearray([0x00,0x00,0x00,0x00,0x00,0x00])
	i2c.readfrom_into(0x70,buf2)
	temp= (buf2[1] | (buf2[0] << 8))*175 /65536.0 - 45.0
	humi= (buf2[4] | (buf2[3] << 8))*100 /65536.0
	print('shtc3:temperature=%f, humidity=%f'%(temp,humi))	



def get_pressure():
	pre_xl=i2c.readfrom_mem(0x5c,0x28,1)
	pre_xl=int.from_bytes(pre_xl,'big')
	pre_l=i2c.readfrom_mem(0x5c,0x29,1)
	pre_l=int.from_bytes(pre_l,'big')
	pre_h=i2c.readfrom_mem(0x5c,0x2a,1)
	pre_h=int.from_bytes(pre_h,'big')
	pre = (pre_h<<16)|(pre_l<<8)|pre_xl
	if pre & 0x00800000:
		pre |= 0xFF000000

	pre = pre/4096.0
	print('lps22hb:pressure=%f Pa'%pre)


def get_gps():
	buf=bytearray()
	uart.write('AT+QGPSCFG=\"gpsnmeatype\",1')
	time.sleep_ms(10)
	bchar=uart.readchar()
	while bchar != -1:
		buf.append(bchar)
		bchar=uart.readchar()
		time.sleep_ms(1)

	buf2=bytearray()
	uart.write('AT+QGPS=1,1,1,1,1')
	time.sleep_ms(10)
	bchar=uart.readchar()
	while bchar != -1:
		buf2.append(bchar)
		bchar=uart.readchar()
		time.sleep_ms(1)

	buf3=bytearray()
	uart.write('AT+QGPSGNMEA=\"GGA\"')
	time.sleep_ms(10)
	bchar=uart.readchar()
	while bchar != -1:
		buf3.append(bchar)
		bchar=uart.readchar()
		time.sleep_ms(1)

	string = str(buf3,'utf-8')
	print(string)

#this function is suitable for most AT commands of bg96. Timeout(ms) is what bg96 needs depending on the AT. e.g. rui.cellular_tx('ATI', 500)
def cellular_tx(at,timeout):
	buf3=bytearray()
	uart.write(at)
	time.sleep_ms(10)
	bchar=uart.readchar()
	while (bchar != -1) or (timeout > 0):
		if bchar != -1:
			buf3.append(bchar)

		bchar=uart.readchar()
		timeout=timeout-1
		time.sleep_ms(1)


	string = str(buf3,'utf-8')
	print(string)
	return string 

#thanks for Mr Dider's contribution
def gnss_on(mode=1, fixmaxtime=30, fixmaxdist=50, fixcount=0, fixrate=1):
  """
  Turns on the GNSS function
  Default parameters
  Checks parameters
  """
  if(mode<1) or (mode>4):
    print("GNSS working mode range 1<>4!")
    print("Default is 1.")
    print("""    1 Stand-alone
    2 MS-based
    3 MS-assisted
    4 Speed-optimal""")
    return
  if(fixmaxtime<1) or (fixmaxtime>255):
    print("Maximum positioning time range 1<>255!")
    print("Default is 30 seconds.")
    return
  if(fixmaxdist<1) or (fixmaxdist>1000):
    print("Accuracy threshold of positioning range 1<>1000!")
    print("Default is 50 meters.")
    return
  if(fixcount>1000):
    print("Number of attempts for positioning range 0<>1000!")
    print("Default is 0 (continuous).")
    return
  if(fixrate<1) or (fixrate>65535):
    print("Interval between first and second positioning range 1<>65535!")
    print("Default is 1 second.")
    return  
  cellular_tx('AT+QGPS='+str(mode)+','+str(fixmaxtime)+','+str(fixmaxdist)+','+str(fixcount)+','+str(fixrate), 500)

def gnss_off():
  """Turns off GNSS"""
  cellular_tx('AT+QGPSEND', 500)

def gnss_status():
  """Enquires GNSS status"""
  cellular_tx('AT+QGPS?', 500)

def gpsloc(mode=0):
  """Acquire Positioning Information
  Modes:
    0: <latitude>,<longitude> format: ddmm.mmmm N/S,dddmm.mmmm E/W
    1: <latitude>,<longitude> format: ddmm.mmmmmm N/S,dddmm.mmmmmm E/W
    2: <latitude>,<longitude> format: (-)dd.ddddd,(-)ddd.ddddd
    Checks mode"""
  if(mode<0) or (mode>2):
    print("GPSLOC mode range 0<>2!")
    print("Default is 0.")
    print("""    Modes:
    0: <latitude>,<longitude> format: ddmm.mmmm N/S,dddmm.mmmm E/W
    1: <latitude>,<longitude> format: ddmm.mmmmmm N/S,dddmm.mmmmmm E/W
    2: <latitude>,<longitude> format: (-)dd.ddddd,(-)ddd.ddddd""")
    return
  cellular_tx('AT+QGPSLOC='+str(mode), 500)

def gnss_enable_nmea():
  cellular_tx('AT+QGPSCFG="nmeasrc",1', 500)

def gnss_disable_nmea():
  cellular_tx('AT+QGPSCFG="nmeasrc",0', 500)

def gnss_get_nmea(sentence="GGA"):
  """gets an NMEA sentence.
  Valid sentences are ¡°GGA¡±,¡°RMC¡±,¡°GSV¡±,¡°GSA¡±,¡°VTG¡±,¡°GNS¡±
  If the sentence is GGA, the code tries to extract data
  and returns it into an object.
  """
  a=cellular_tx('AT+QGPSGNMEA="'+sentence+'"', 500)
  b=a.split("\n")
  for x in b:
    if(x.startswith('+QGPSGNMEA: $GPGGA')):
      c=x[12:]
      c=c.split(',')
      result={}
      time=c[1].split('.')
      time=time[0]
      result['tof']=time[0:2]+':'+time[2:4]+':'+time[4:]+' UTC'
      valid=c[6]
      if(valid==0):
        print("  Fix is not valid! Aborting.")
        result['valid']=False
        return result
      result['valid']=True
      SVs=c[7]
      result['SVs']=float(SVs)
      OrthoHeight=c[9]+' '+c[10]
      result['orthoheight']=float(c[9])
      long=float(c[2])
      NS=c[3]
      x=int(long/100)
      y=((long/100)-x)*10/6
      long=x+y
      result['long']=long
      result['NS']=NS
      lat=float(c[4])
      EW=c[5]
      x=int(lat/100)
      y=((lat/100)-x)*10/6
      lat=x+y
      result['lat']=long
      result['EW']=EW
      return result
