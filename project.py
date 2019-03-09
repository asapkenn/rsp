import lcddriver
import time
import picamera
import time
import RPi.GPIO as GPIO
import RPi.GPIO as GPIO
import MFRC522
import signal
import datetime
from PIL import Image
import pytesseract
import sqlite3
from datetime import datetime 

display = lcddriver.lcd()
GPIO.setmode(GPIO.BCM)

continue_reading = True
signal.signal(signal.SIGINT, end_read)
MIFAREReader = MFRC522.MFRC522()

dbconn = sqlite3.connect('plates.sqlite')
dbcur = dbconn.cursor()

carsensor0=17
carsensor1=27
carsensor2=22
carsensor3=23
carsensor4=18
carsensor5=25
carsensor6=12
carsensor7=16

servo1=20
servo2=21
servo_gate=26

GPIO.setup(servo1,GPIO.OUT)
GPIO.setup(servo2,GPIO.OUT)
GPIO.setup(servo_gate,GPIO.OUT)
pwmgate=GPIO.PWM(servo_gate,50)

def car_sensors(sensorPin):
  status_sensor=[]
  for i in range(5):
    GPIO.setup(sensorPin,GPIO.IN)
    sensor=GPIO.input(sensorPin)
    if sensor == 1:
      status_sensor.append(1.)
    elif sensor == 0:
      status_sensor.append(0.)
    time.sleep(0.2)
  av = reduce(lambda x, y: x + y, status_sensor) / len(status_sensor)
  if av > 0.4:
    return 1
  else:
    return 0

def display(row1='->',row2='->'):
  try:
    while True:
      print("Writing to display")
      display.lcd_display_string(row1, 1) 
      display.lcd_display_string(row2, 2) 
      time.sleep(3)                                  
      display.lcd_clear()                              
      #time.sleep(2)                                    
  except:
      pass
            
def move_camera(servoPin,desired_angle):
  pwm=GPIO.PWM(servoPin,50)
  pwm.start(7)
  dc=1./18.*(desired_angle)+2
  pwm.ChangeDutyCycle(dc)

def end_read(signal,frame):
  global continue_reading
  print "Ctrl+C captured, ending read."
  continue_reading = False
  GPIO.cleanup()

def check_for_outgoing_cars():
  incoming_car=car_sensors(carsensor6)
  if incoming_car:
    return 1
  else:
    return 0

def check_for_incoming_cars():
  outgoing_car=car_sensors(carsensor7)
  if outgoing_car:
    return 1
  else:
    return 0

def space_checker():
  unpacked_spaces=[]
  cs0=car_sensors(carsensor0)
  cs1=car_sensors(carsensor1)
  cs2=car_sensors(carsensor2)
  cs3=car_sensors(carsensor3)
  cs4=car_sensors(carsensor4)
  cs5=car_sensors(carsensor5)
  if cs0==1:
    pass
  else:
    unpacked_spaces.append('cs0')

  if cs1==1:
    pass
  else:
    unpacked_spaces.append('cs1')

  if cs2==1:
    pass
  else:
    unpacked_spaces.append('cs2')

  if cs3==1:
    pass
  else:
    unpacked_spaces.append('cs3')

  if cs4==1:
    pass
  else:
    unpacked_spaces.append('cs4')

  if cs5==1:
    pass
  else:
    unpacked_spaces.append('cs5')

  if len(unpacked_spaces) > 0:
    return 1,unpacked_spaces
  else:
    return 0,unpacked_spaces

def rfidreader():
  t1 = datetime.now()
  while (datetime.now()-t1).seconds <= 25:   
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status == MIFAREReader.MI_OK:
        print "Card detected"
        return 1
    else:
        print 'no card'
  return 0

def gate_opener():
  pwmgate.start(7)
  desired_angle=140
  desired_angle2=45
  dc1=1./18.*(desired_angle)+2
  pwmgate.ChangeDutyCycle(dc1)
  time.sleep(15)
  dc2=1./18.*(desired_angle2)+2
  pwmgate.ChangeDutyCycle(dc2)

def move_camera_right():
  move_camera(100,servo2)
  move_camera(180,servo1)
  move_camera(60,servo2)

def move_camera_left():
  move_camera(100,servo2)
  move_camera(0,servo1)
  move_camera(60,servo2)

def take_pic():
  filename=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+'.jpg'
  camera = PiCamera(resolution=(1280, 720), framerate=30)
  camera.iso = 100
  time.sleep(5)
  camera.shutter_speed = camera.exposure_speed
  camera.exposure_mode = 'off'
  g = camera.awb_gains
  camera.awb_mode = 'off'
  camera.awb_gains = g
  camera.capture(filename)
  process_car_plates(filename) 

def process_car_plates(picname):
  pic_cont = pytesseract.image_to_string(Image.open(picname))
  dbcur.execute("INSERT INTO plates_numbers (plate_no) VALUES (?);", (pic_cont.strip('\n'),))

while True:
  full_packed,empty_slots=space_checker()
  if full_packed==1:
    display('Parking Available',str(len(empty_slots))+' slots available')
  else:
    display('Parking Fully Parked','No available slots')
  if check_for_outgoing_cars():
    display('Outgoing Car','Processing...')
    move_camera_right()
    take_pic()
    display('Place your Card ','for processing...')
    if rfidreader():
      gate_opener()
    else:
      pass
    display('Restaring services ',' in a second...')
    time.sleep(1)
  if check_for_incoming_cars():
    display('Incoming Car','Processing...')
    move_camera_left()
    take_pic()
    display('Place your Card ','for processing...')
    if rfidreader():
      gate_opener()
    else:
      pass
    display('Restaring services ',' in a second...')
    time.sleep(1)

