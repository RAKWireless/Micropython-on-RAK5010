#this file is the init script of 5010, inlude bg96 and other sensors.
#use ampy --port /dev/ttyACM0 put init.py to your board

import time
from machine import Pin
from machine import UART
from machine import I2C


#bg96 pin define
bg96_status_pin=Pin(16,Pin.IN)
bg96_reset_pin=Pin(28,Pin.OUT)
bg96_power_key_pin= Pin(2,Pin.OUT)
bg96_w_disable_pin=Pin(29,Pin.OUT)
bg96_dtr_pin=Pin(26,Pin.IN)
bg96_ap_ready_pin=Pin(30,Pin.IN)
bg96_psm_pin=Pin(3,Pin.IN)
bg96_gps_en=Pin(39,Pin.OUT)

print('****************************************5010 board init begin!****************************************')
#bg96 power up
print('bg96 power up!')
bg96_reset_pin.value(0)
bg96_power_key_pin.value(1)
bg96_w_disable_pin.value(1)
time.sleep_ms(2000)
bg96_power_key_pin.value(0)
bg96_gps_en.value(1)

uart=UART(0,115200)
print('bg96 version:')
buf=bytearray()
uart.write('ATI')
time.sleep_ms(10)
bchar=uart.readchar()
while bchar != -1:
	buf.append(bchar)
	bchar=uart.readchar()
	time.sleep_ms(1)

string = str(buf,'utf-8')
print(string)

#i2c obj
i2c=I2C(1,13,14)
print('I2C device address on bus:')
print('I2c scan ...')
device_list=i2c.scan()
if len(device_list) == 4:
	print('lis3dh address is 0x%x' % device_list[0])
	print('opt3001 address is 0x%x' % device_list[1])
	print('lps22hb address is 0x%x' % device_list[2])
	print('shtc3 address is 0x%x' % device_list[3])
else:
	print('no i2c device')

#lis3dh init addr-0x19
buf=bytearray([0x57])
i2c.writeto_mem(0x19,0x20,buf)
buf=bytearray([0x08])
i2c.writeto_mem(0x19,0x23,buf)
lis3dh_id=i2c.readfrom_mem(0x19,0x0F,1)
lis3dh_id=''.join(['%02X' %x  for x in lis3dh_id])
print('I2C device lis3dh init and id is 0x',lis3dh_id)

#shtc3 init addr-0x70
buf0=bytearray([0x35,0x17])
i2c.writeto(0x70,buf0)
time.sleep_ms(500)
buf=bytearray([0xEF,0xC8])
i2c.writeto(0x70,buf)
i2c.readfrom_into(0x70,buf)
num=int.from_bytes(buf,'big')
print('I2C device shtc3 init and id is %d'%num)

#opt3001 init addr-0x44
buf=bytearray([0xCC,0x10])
i2c.writeto_mem(0x44,0x01,buf)
manufacture_id=i2c.readfrom_mem(0x44,0x7E,2)
num=int.from_bytes(manufacture_id,'big')
print('I2C device opt3001 init and manufacture id is %d'%num)
device_id=i2c.readfrom_mem(0x44,0x7F,2)
num=int.from_bytes(device_id,'big')
print('I2C device opt3001 init and device id is %d'%num)

#lps22hb init addr-0x5c
buf=bytearray([0x50])
i2c.writeto_mem(0x5c,0x10,buf)
lps22hb_id=i2c.readfrom_mem(0x5c,0x0F,1)
lps22hb_id=''.join(['%02X' %x  for x in lps22hb_id])
print('I2C device lps22hb init and id is 0x',lps22hb_id)

print('****************************************5010 board init finish!****************************************')






