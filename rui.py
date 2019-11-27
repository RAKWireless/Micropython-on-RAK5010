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

#this function is suit for most at commands of bg96. Timeout(ms) is the what bg96 needs depending on the at. e.g. rui.cellular_tx('ATI',500)
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
