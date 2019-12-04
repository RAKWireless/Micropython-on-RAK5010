#this file is the rui script of 5010, inludes bg96 and other sensors.
#use ampy --port /dev/ttyACM0 put rui.py to your board

import time
import math
from machine import Pin
from machine import UART
from machine import I2C

i2c=I2C(1, 13, 14)
uart=UART(0, 115200)

def get_acceleration(echo=False, ret=True):
  x_l=i2c.readfrom_mem(0x19, 0x28, 1)
  x_h=i2c.readfrom_mem(0x19, 0x29, 1)
  y_l=i2c.readfrom_mem(0x19, 0x2a, 1)
  y_h=i2c.readfrom_mem(0x19, 0x2b, 1)
  z_l=i2c.readfrom_mem(0x19, 0x2c, 1)
  z_h=i2c.readfrom_mem(0x19, 0x2d, 1)
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
  echo_Arg='lis3dh: acc_x='+str(acc_x)+', acc_y='+str(acc_y)+', acc_z='+str(acc_z)
  ret_Arg={}
  ret_Arg['x']=acc_x
  ret_Arg['y']=acc_y
  ret_Arg['z']=acc_z
  return _answer(echo, ret, echo_Arg, ret_Arg)

def get_light_strength(echo=False, ret=True):
  buf=i2c.readfrom_mem(0x44, 0x00, 2)
  light=int.from_bytes(buf, 'big')
  m=light & 0x0FFF
  e=(light & 0xF000) >> 12
  h= math.pow(2, e)
  light = m*(0.01 * h)
  echo_Arg='opt3001: Light strength = '+str(light)
  ret_Arg=light
  return _answer(echo, ret, echo_Arg, ret_Arg)

def get_temperature_humidity(echo=False, ret=True):
  buf=bytearray([0x7C, 0xA2])
  i2c.writeto(0x70, buf)
  buf2=bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
  i2c.readfrom_into(0x70, buf2)
  temp = (buf2[1] | (buf2[0] << 8)) * 175 / 65536.0 - 45.0
  humi = (buf2[4] | (buf2[3] << 8)) * 100 / 65536.0
  echo_Arg='shtc3: Temperature='+str(temp)+', Humidity='+str(humi)
  ret_Arg={}
  ret_Arg['temp']=temp
  ret_Arg['humi']=humi
  return _answer(echo, ret, echo_Arg, ret_Arg)

def get_pressure(echo=False, ret=True):
  pre_xl=i2c.readfrom_mem(0x5c, 0x28, 1)
  pre_xl=int.from_bytes(pre_xl, 'big')
  pre_l=i2c.readfrom_mem(0x5c, 0x29, 1)
  pre_l=int.from_bytes(pre_l, 'big')
  pre_h=i2c.readfrom_mem(0x5c, 0x2a, 1)
  pre_h=int.from_bytes(pre_h, 'big')
  pre = (pre_h<<16)|(pre_l<<8)|pre_xl
  if pre & 0x00800000:
    pre |= 0xFF000000
  pre = pre/4096.0
  echo_Arg='lps22hb: Pressure='+str(pre)+' HPa'
  ret_Arg=pre
  return _answer(echo, ret, echo_Arg, ret_Arg)

def get_gps(echo=False, ret=True):
  buf=bytearray()
  uart.write('AT+QGPSCFG=\"gpsnmeatype\", 1')
  time.sleep_ms(10)
  bchar=uart.readchar()
  while bchar != -1:
    buf.append(bchar)
    bchar=uart.readchar()
    time.sleep_ms(1)
  buf2=bytearray()
  uart.write('AT+QGPS=1, 1, 1, 1, 1')
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
  string = str(buf3, 'utf-8')
  return _answer(echo, ret, string, string)

#this function is suitable for most AT commands of bg96. Timeout(ms) is what bg96 needs depending on the AT. e.g. rui.cellular_tx('ATI', 500)
def cellular_tx(at, timeout=500, echo=True, ret=False):
  """Improved command. Added two variables:
   . echo: should we print the result?
   . ret:  should we return the result as a string?
   This later feature is used by some functions below to display info in a better format."""
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
  string = str(buf3, 'utf-8')
  return _answer(echo, ret, string, string)
  ## Using this string in gnss_get_nmea() for instance, to extract data.

### Contribution by Kongduino

_bg96_errors={}
_bg96_errors[0]="Phone failure"
_bg96_errors[1]="No connection to phone"
_bg96_errors[2]="Phone-adaptor link reserved"
_bg96_errors[3]="Operation not allowed"
_bg96_errors[4]="Operation not supported"
_bg96_errors[5]="PH-SIM PIN required"
_bg96_errors[6]="PH-FSIM PIN required"
_bg96_errors[7]="PH-FSIM PUK required"
_bg96_errors[10]="(U)SIM not inserted"
_bg96_errors[11]="(U)SIM PIN required"
_bg96_errors[12]="(U)SIM PUK required"
_bg96_errors[13]="(U)SIM failure"
_bg96_errors[14]="(U)SIM busy"
_bg96_errors[15]="(U)SIM wrong"
_bg96_errors[16]="Incorrect password"
_bg96_errors[17]="(U)SIM PIN2 required"
_bg96_errors[18]="(U)SIM PUK2 required"
_bg96_errors[20]="Memory full"
_bg96_errors[21]="Invalid index"
_bg96_errors[22]="Not found"
_bg96_errors[23]="Memory failure"
_bg96_errors[24]="Text string too long"
_bg96_errors[25]="Invalid characters in text string"
_bg96_errors[26]="Dial string too long"
_bg96_errors[27]="Invalid characters in dial string"
_bg96_errors[30]="No network service"
_bg96_errors[31]="Network timeout"
_bg96_errors[32]="Network not allowed - emergency calls only"
_bg96_errors[40]="Network personalization PIN required"
_bg96_errors[41]="Network personalization PUK required"
_bg96_errors[42]="Network subset personalization PIN required"
_bg96_errors[43]="Network subset personalization PUK required"
_bg96_errors[44]="Service provider personalization PIN required"
_bg96_errors[45]="Service provider personalization PUK required"
_bg96_errors[46]="Corporate personalization PIN required"
_bg96_errors[47]="Corporate personalization PUK required"
_bg96_errors[300]="ME failure"
_bg96_errors[301]="SMS ME reserved"
_bg96_errors[302]="Operation not allowed"
_bg96_errors[303]="Operation not supported"
_bg96_errors[304]="Invalid PDU mode"
_bg96_errors[305]="Invalid text mode"
_bg96_errors[310]="(U)SIM not inserted"
_bg96_errors[311]="(U)SIM pin necessary"
_bg96_errors[312]="PH (U)SIM pin necessary"
_bg96_errors[313]="(U)SIM failure"
_bg96_errors[314]="(U)SIM busy"
_bg96_errors[315]="(U)SIM wrong"
_bg96_errors[316]="(U)SIM PUK required"
_bg96_errors[317]="(U)SIM PIN2 required"
_bg96_errors[318]="(U)SIM PUK2 required"
_bg96_errors[320]="Memory failure"
_bg96_errors[321]="Invalid memory index"
_bg96_errors[322]="Memory full"
_bg96_errors[330]="SMSC address unknown"
_bg96_errors[331]="No network"
_bg96_errors[332]="Network timeout"
_bg96_errors[501]="Invalid parameter"
_bg96_errors[502]="Operation not supported"
_bg96_errors[503]="GNSS subsystem busy"
_bg96_errors[504]="Session is ongoing"
_bg96_errors[505]="Session not active"
_bg96_errors[506]="Operation timeout"
_bg96_errors[507]="Function not enabled"
_bg96_errors[508]="Time information error"
_bg96_errors[509]="XTRA not enabled"
_bg96_errors[512]="Validity time is out of range"
_bg96_errors[513]="Internal resource error"
_bg96_errors[514]="GNSS locked"
_bg96_errors[515]="End by E911"
_bg96_errors[516]="Not fixed now"
_bg96_errors[517]="Geo-fence ID does not exist"
_bg96_errors[549]="Unknown error"

def _answer(echo, ret, echo_Arg, ret_Arg):
  if(echo):
    print(echo_Arg)
  if(ret):
    return ret_Arg

def gnss_on(mode=1, fixmaxtime=30, fixmaxdist=50, fixcount=0, fixrate=1, echo=True, ret=False):
  """
  Turns on the GNSS function
  Default parameters
  Checks parameters before sending, or fails.
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
  result=cellular_tx('AT+QGPS='+str(mode)+','+str(fixmaxtime)+','+str(fixmaxdist)+','+str(fixcount)+','+str(fixrate), 500, False, True).replace('\r', '').strip()
  return _answer(echo, ret, result, result)

def gnss_off(echo=True, ret=False):
  """Turns off GNSS"""
  result=cellular_tx('AT+QGPSEND', 500, False, True).replace('\r', '').strip()
  return _answer(echo, ret, result, result)

def gnss_status(echo=True, ret=False):
  """Enquires GNSS status"""
  result=cellular_tx('AT+QGPS?', 500, False, True).replace('\r', '').strip()
  if(result.startswith('AT+QGPS?\n+QGPS: ')):
    #Correct result
    a=result.split(': ')[1].split('\n')[0]
    if(a=='0'):
      echo_Arg="GNSS OFF"
    if(a=='1'):
      echo_Arg="GNSS ON"
    ret_Arg=echo_Arg
  else:
    echo_Arg="Unknown result response:\n  "+result
    ret_Arg={}
  return _answer(echo, ret, echo_Arg, ret_Arg)

def gpsloc(mode=0, echo=False, ret=True):
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
  result=cellular_tx('AT+QGPSLOC='+str(mode), 500, False, True).replace('\r', '').strip()
  if(result.find('\n+CME ERROR: ')>-1):
    #'AT+QGPSLOC=0\n+CME ERROR: 516'
    a=int(result.split(': ')[1].split('\n')[0].split(',')[0])
    ret_Arg={}
    ret_Arg['code']=a
    ret_Arg['text']=_bg96_errors[a]
  if(result.find('\n+QGPSLOC: ')>-1):
    #+QGPSLOC: <UTC>,<latitude>,<longitude>,<hdop>,<altit ude>,<fix>,<cog>,<spkm>,<spkn>,<date>,<nsat>
    #we have a match
    a=result.split(': ')[1].split('\n')[0].split(',')
    ret_Arg={}
    time=a[0].split('.')[0]
    ret_Arg['tof']=time[0:2]+':'+time[2:4]+':'+time[4:]+' UTC'
    NS="N"
    EW="E"
    if(mode==2):
      #long/lat format [-]dd.ddddd
      if(a[1][0:1]=='-'):
        NS="S"
        a[1]=a[1][1:]
      if(a[2][0:1]=='-'):
        EW="W"
        a[2]=a[2][1:]
    else:
      #long/lat format ddmm.mmmm[mm] N/S,dddmm.mmmm[mm] E/W
      NS=a[1][-1]
      a[1]=a[1][:-1]
      EW=a[2][-1]
      a[2]=a[2][:-1]
      long=float(a[1])
      x=int(long/100)
      y=((long/100)-x)*10/6
      long=x+y
      ret_Arg['long']=long
      ret_Arg['NS']=NS
      lat=float(a[2])
      x=int(lat/100)
      y=((lat/100)-x)*10/6
      lat=x+y
      ret_Arg['lat']=lat
      ret_Arg['EW']=EW
      ret_Arg['hdop']=float(a[3])
      ret_Arg['altitude']=float(a[4])
      ret_Arg['fix']=a[5]+"D positioning"
      ret_Arg['cog']=float(a[6])
      ret_Arg['spkm']=float(a[7])
      ret_Arg['spkn']=float(a[8])
      date=a[9]
      ret_Arg['date']="20"+date[4:][0:2]+'/'+date[2:4]+'/'+date[0:2]
      ret_Arg['nsat']=float(a[10])
      ret_Arg['text']=result.split(': ')[1].split('\n')[0]
  return _answer(echo, ret, ret_Arg['text'], ret_Arg)

def gnss_enable_nmea():
  print(cellular_tx('AT+QGPSCFG="nmeasrc",1', 500, False, True).replace('\r', '').strip())

def gnss_disable_nmea():
  print(cellular_tx('AT+QGPSCFG="nmeasrc",0', 500, False, True).replace('\r', '').strip())

def gnss_get_nmea(sentence="GGA"):
  """gets an NMEA sentence.
  Valid sentences are “GGA”,“RMC”,“GSV”,“GSA”,“VTG”,“GNS”
  If the sentence is GGA, the code tries to extract data
  and returns it into an object.
  """
  a=cellular_tx('AT+QGPSGNMEA="'+sentence+'"', 500, False, True)
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
      result['lat']=lat
      result['EW']=EW
      return result

def bg96_PI(echo=False, ret=True):
  """Gets the full Product Information.
  Equivalent to the next three commands plus bg96_IMEI."""
  result=cellular_tx('ATI', 300, False, True).replace('\r', '').strip().split('\n')
  # Since the IMEI is part of the product info, no reason not to get it together.
  IMEI=bg96_IMEI(False, True)
  echo_Arg="Manufacturer: "+result[1]+"\nProduct: "+result[2]+"\n"+result[3]+"\nIMEI: "+IMEI
  a={}
  a['manufacturer']=result[1]
  a['product']=result[2]
  a['revision']=result[3].split(': ')[1]
  a['IMEI']=IMEI
  return _answer(echo, ret, echo_Arg, a)

def bg96_Manufacturer(echo=False, ret=True):
  """Gets the Manufacturer's Name'"""
  result=cellular_tx('AT+GMI', 300, False, True).replace('\r', '').strip().split('\n')
  return _answer(echo, ret, "Manufacturer: "+result[1], result[1])

def bg96_Product(echo=False, ret=True):
  """Gets the Product Name"""
  result=cellular_tx('AT+GMM', 300, False, True).replace('\r', '').strip().split('\n')
  return _answer(echo, ret, "Product: "+result[1], result[1])

def bg96_Revision(echo=False, ret=True):
  """Gets the Software Revision"""
  result=cellular_tx('AT+GMR', 300, False, True).replace('\r', '').strip().split('\n')
  return _answer(echo, ret, "Revision: "+result[1], result[1])

def bg96_IMEI(echo=False, ret=True):
  """Gets the Device's IMEI'"""
  result=cellular_tx('AT+GSN', 300, False, True).replace('\r', '').strip().split('\n')
  return _answer(echo, ret, "IMEI: "+result[1], result[1])

def bg96_IMSI(echo=False, ret=True):
  """Query IMSI number of (U)SIM"""
  result=cellular_tx('AT+CIMI', 300, False, True).replace('\r', '').strip().split('\n')
  return _answer(echo, ret, "IMSI: "+result[1], result[1])

def bg96_ICCID(echo=False, ret=True):
  """Gets the ICCID of the (U)SIM card'"""
  result=cellular_tx('AT+QCCID', 300, False, True).replace('\r', '').strip().split('\n')
  return _answer(echo, ret, "CCID: "+result[1], result[1])

_insertStatus=[]
_insertStatus.append('(U)SIM card is removed.')
_insertStatus.append('(U)SIM card is inserted.')
_insertStatus.append('(U)SIM card status unknown, before (U)SIM initialization.')

def bg96_SIM_Insertion(echo=False, ret=True):
  """Query (U)SIM card insertion status."""
  result=cellular_tx('AT+QSIMSTAT?', 300, False, True).replace('\r', '').strip()
  if(result.find('\n+QSIMSTAT: ')>-1):
    #AT+QSIMSTAT?\n+QSIMSTAT: 1,0
    a=result.split('\n')[1].split(': ')[1].split(',')
    if(a[0]=='0'):
      echo_Arg="(U)SIM card insertion status report dis"
    else:
      echo_Arg="(U)SIM card insertion status report en"
    echo_Arg+="abled.\n"+_insertStatus[int(a[1])]
    ret_Arg={}
    ret_Arg['enabled']=(a[0]=='1')
    ret_Arg['statusCode']=int(a[1])
    ret_Arg['status']=_insertStatus[int(a[1])]
  else:
    echo_Arg=result
    ret_Arg=result
  return _answer(echo, ret, echo_Arg, ret_Arg)

def bg96_FactoryDefault():
  """Resets the device to Factory Default"""
  result=cellular_tx('AT&F', 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Config():
  """Gets the Current Configuration"""
  result=cellular_tx('AT&V', 300, False, True).replace('\r', '').strip()
  result=result.replace('\n', '\nAT')
  result=result[:-7]
  print(result)

def bg96_Save_User_Profile():
  """Saves the Current Configuration to the USer Profile"""
  result=cellular_tx('AT&W', 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Load_User_Profile():
  """Loads the User Profile Configuration"""
  result=cellular_tx('ATZ', 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Set_Result_Code(code=0):
  """Sets the Result Code Display to ON or OFF"""
  if(code<0) or (code>1):
    print("Use 0 for yes or")
    print("1 for no")
    return
  result=cellular_tx('ATQ'+str(code), 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Result_code_On():
  """Sets the Result Code Display to ON"""
  result=cellular_tx('ATQ0', 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Result_code_Off():
  """Sets the Result Code Display to OFF"""
  result=cellular_tx('ATQ1', 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Set_Result_Code_Verbosity(code=0):
  """Sets the Result Code Verbosity"""
  if(code<0) or (code>1):
    print("Use 0 for non-verbose or")
    print("1 for verbose")
    return
  result=cellular_tx('ATV'+str(code), 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Set_Command_Echo(code=0):
  """Sets the Command Echo to ON or OFF"""
  if(code<0) or (code>1):
    print("Use 0 for echo off or")
    print("1 for echo on")
    return
  result=cellular_tx('ATE'+str(code), 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Power_Down(code=1):
  """Powers down the device"""
  if(code<0) or (code>1):
    print("Use 0 for immediate power down or")
    print("1 for normal power down")
    return
  result=cellular_tx('AT+QPOWD'+str(code), 300, False, True).replace('\r', '').strip()
  print(result)

def bg96_Read_Clock(echo=False, ret=True):
  """Gets the time from the RTC
  Returns a dict with two key/value pairs
  date: yy/mm/dd
  time: hh:mm:ss
  """
  result=cellular_tx('AT+CCLK?', 300, False, True).replace('\r', '').strip()
  if(result.find('\n+CCLK: ')>-1):
    #AT+CCLK?\n+CCLK: "80/01/06,01:24:14"
    a=result.split('"')[1]
    echo_Arg=a
    a=a.split(',')
    ret_Arg={}
    ret_Arg['date']=a[0]
    ret_Arg['time']=a[1]
  else:
    echo_Arg=result
    ret_Arg=result
  return _answer(echo, ret, echo_Arg, ret_Arg)

def bg96_Battery(echo=False, ret=True):
  """Gets the battery charging status
  Returns a dict with four key/value pairs
  code: [012]
  volt: <float>
  charging: True/False
  percent: <float>
  """
  result=cellular_tx('AT+CBC', 300, False, True).replace('\r', '').strip()
  if(result.startswith('AT+CBC\n+CBC: ')):
    a=result.split(': ')[1].split('\n')[0].split(',')
    if(a[0]=='0'):
      echo_Arg="Not charging... ["+a[1]+"% "+str(float(a[2])/1000)+"V]"
    if(a[0]=='1'):
      echo_Arg="Charging: "+a[1]+"% "+str(float(a[2])/1000)+"V"
    if(a[0]=='2'):
      echo_Arg="Done charging: "+a[1]+"% "+str(float(a[2])/1000)+"V"
    ret_Arg={}
    ret_Arg['code']=int(a[0])
    ret_Arg['charging']=(a[0]=='1')
    ret_Arg['percent']=float(a[1])
    ret_Arg['volt']=float(a[2])/1000
  else:
    echo_Arg=result
    ret_Arg={}
  return _answer(echo, ret, echo_Arg, ret_Arg)

def bg96_Temp(echo=False, ret=True):
  """Gets the temperature for PMIC, XO and PA"""
  result=cellular_tx('AT+QTEMP', 300, False, True).replace('\r', '').strip()
  if(result.startswith('AT+QTEMP\n+QTEMP: ')):
    a=result.split(': ')[1].split('\n')[0].split(',')
    ret_Arg={}
    ret_Arg['PMIC']=float(a[0])
    ret_Arg['XO']=float(a[1])
    ret_Arg['PA']=float(a[2])
    echo_Arg="PMIC: "+a[0]+" C\nXO:   "+a[1]+" C\nPA:   "+a[2]+" C"
  else:
    echo_Arg="Unknown result code:\n  "+result
    ret_Arg={}
  return _answer(echo, ret, echo_Arg, ret_Arg)

_br9600=9600
_br19200=19200
_br38400=38400
_br57600=57600
_br115200=115200
_br230400=230400
_br460800=460800
_br921600=921600

def bg96_Set_Baud_Rate(rate=115200, echo=False, ret=True):
  result=cellular_tx('AT+IPR='+str(rate), 300, False, True).replace('\r', '').strip()
  return _answer(echo, ret, result, result)

_cpasStatus=[]
_cpasStatus.append('Ready')
_cpasStatus.append('Ringing')
_cpasStatus.append('Call in progress or call hold')

def bg96_Activity_Status(echo=False, ret=True):
  result=cellular_tx('AT+CPAS', 300, False, True).replace('\r', '').strip().split('\n')[1]
  if(result.startswith('+CPAS: ')):
    a=int(result.split(': ')[1])
    ret_Arg={}
    ret_Arg['code']=a
    ret_Arg['text']=_cpasStatus[a]
    echo_Arg=_cpasStatus[a]+" ["+str(a)+"]"
  else:
    ret_Arg=result
    echo_Arg=result
  return _answer(echo, ret, echo_Arg, ret_Arg)
