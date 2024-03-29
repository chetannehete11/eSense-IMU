cimport pexpect
import time
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation



def hexStrToInt(hexstr1, hexstr2):
    val = int(hexstr2,16) + (int(hexstr1,16)<<8)
    if ((val&0x8000)==0x8000): # treat signed 16bits
        val = -((val^0xffff)+1)
    return val


def getGyroValues(hexstr):
    gyro_x = hexStrToInt(hexstr[12:14], hexstr[15:17])/65.5
    gyro_y = hexStrToInt(hexstr[18:20], hexstr[21:23])/65.5
    gyro_z = hexStrToInt(hexstr[24:26], hexstr[27:29])/65.5

    return gyro_x, gyro_y, gyro_z


def getAcclValues(hexstr):
    accl_x = (hexStrToInt(hexstr[30:32], hexstr[33:35])/8192)*9.80665
    accl_y = (hexStrToInt(hexstr[36:38], hexstr[39:41])/8192)*9.80665
    accl_z = (hexStrToInt(hexstr[42:44], hexstr[45:47])/8192)*9.80665

    return accl_x, accl_y, accl_z




last_read_time = 0.0

last_x_angle = 0.0
last_y_angle = 0.0
last_z_angle = 0.0

def c_filtered_angle(ax_angle, ay_angle, gx_angle, gy_angle):
    alpha = 0.98
    c_angle_x = alpha*gx_angle + (1.0 - alpha)*ax_angle
    c_angle_y = alpha*gy_angle + (1.0 - alpha)*ay_angle
    return (c_angle_x, c_angle_y)

def get_last_time():
    return last_read_time

def get_last_x_angle():
    return last_x_angle

def get_last_y_angle():
    return last_y_angle

def get_last_z_angle():
    return last_z_angle

def gyr_angle(Gx, Gy, Gz, dt):
    gx_angle = Gx*dt + get_last_x_angle()
    gy_angle = Gy*dt + get_last_y_angle()
    gz_angle = Gz*dt + get_last_z_angle()
    return (gx_angle, gy_angle, gz_angle)

def acc_angle(Ax, Ay, Az):
    radToDeg = 180/3.14159
    ax_angle = math.atan(Ay/math.sqrt(math.pow(Ax,2) + math.pow(Az, 2)))*radToDeg
    ay_angle = math.atan((-1*Ax)/math.sqrt(math.pow(Ay,2) + math.pow(Az, 2)))*radToDeg
    return (ax_angle, ay_angle)


def set_last_read_angles(x, y):
    global last_x_angle, last_y_angle
    last_x_angle = x
    last_y_angle = y




DEVICE = "00:04:79:00:0d:ca"

print("eSense address:"),
print(DEVICE)

# Run gatttool interactively.
print("Run gatttool...")
child = pexpect.spawn("gatttool -I")

# Connect to the device.
print("Connecting to "),
print(DEVICE),
child.sendline("connect {0}".format(DEVICE))
child.expect("Connection successful", timeout=5)
print(" Connected!")

child.sendline("char-read-hnd 0x0c")
child.expect("Characteristic value/descriptor: ", timeout=10)
child.expect("\r\n", timeout=10)
print("Start/Stop Value: {0} ".format(child.before.decode("utf-8")))

print("Starting the IMU data sampling....")

child.sendline("char-write-req 0x0c 5335020132")
child.expect("Characteristic value was written successfully", timeout=10)
child.expect("\r\n", timeout=10)
print("Write successful, IMU started publishing")


while True:
    #try:
    child.sendline("char-read-hnd 0x000e")
    child.expect("Characteristic value/descriptor: ", timeout=10)
    #child.expect("\r\n", timeout=10)
    #print("Raw values: ",child.before.decode("utf-8").split('\r\n'))
    raw = child.before.decode("utf-8").split('\r\n')
    #print(raw)

    try:
        for i in range(1,len(raw)):
            if(len(raw[i]) > 100):
                imu_data = raw[i]
                #print(imu_data)
                #print(len(raw))
                #print(imu_data[76:123])
                imu_values = imu_data[76:123]

                _imu_values = imu_values[12:14]

                #print(imu_values[12:47])
                gyro_x, gyro_y, gyro_z = getGyroValues(imu_values)
                accl_x, accl_y, accl_z = getAcclValues(imu_values)
               # print("Gyroscope Reading: {0:.3f} {1:.3f} {2:.3f}".format(gyro_x, gyro_y, gyro_z))
               # print("Accelerometer Reading: {0:.3f} {1:.3f} {2:.3f}".format(accl_x, accl_y, accl_z))

                print("\n")

                #t_now = time.ticks_ms()    #The Error is happening here
                #print(t_now)
                #dt = (t_now - get_last_time())/1000
                dt =  1/50

                # Calculate angle of inclination or tilt for the x and y axes with acquired acceleration vectors
                acc_angles = acc_angle(accl_x, accl_y, accl_z)
                gyr_angles = gyr_angle(gyro_x, gyro_y, gyro_z, dt)
               # print(acc_angles)
                #print(gyr_angles)

                # filtered tilt angle
                (c_angle_x, c_angle_y) = c_filtered_angle(acc_angles[0], acc_angles[1], gyr_angles[0], gyr_angles[1]) 
                print(c_angle_x)
                print(c_angle_y)
                set_last_read_angles( c_angle_x, c_angle_y)

    except:
        print("not")
        pass



