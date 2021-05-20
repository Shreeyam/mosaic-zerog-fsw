from mvIMPACT import acquire
from sense_hat import SenseHat
from opto import Opto
import numpy as np
import ctypes
import time

# config
N_VALUES = 64
START = -20
STOP = 120
LENS_ADDRESS = "/dev/serial/by-id/usb-Optotune_LD_Optotune_LD_5573633373635141E081-if00"

# Initialise devices
sense = SenseHat()
# clear to red
sense.low_light = True
sense.clear((255, 0, 0))
sense.set_imu_config(True, True, True)
devMgr = acquire.DeviceManager()
pDev = devMgr.getDevice(0)

# Set up camera and get the function interface
pDev.open()
ac = acquire.CameraSettingsBlueFOX(pDev)
ac.expose_us.write(10)
ac.binningMode.write(acquire.cbmBinningHV)

# Get the function interface
fi = acquire.FunctionInterface(pDev)

# lens values to cycle through
lens_values = np.linspace(START, STOP, N_VALUES)
o = Opto(port=LENS_ADDRESS)
o.connect()

def recordImage(filename):
    fi.imageRequestSingle()
    requestNr = fi.imageRequestWaitFor(1000)

    if(fi.isRequestNrValid(requestNr)):
        pRequest = fi.getRequest(requestNr)

        if pRequest.isOK:
            size = pRequest.imageSize.read()
            cbuf = (ctypes.c_char * size).from_address(int(pRequest.imageData.read()))
            print(f"{size}, {requestNr}, {pRequest}")
            channelType = np.uint16 if pRequest.imageChannelBitDepth.read() > 8 else np.uint8
            image = np.frombuffer(cbuf, dtype=channelType)
            image.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), pRequest.imageChannelCount.read())
            del cbuf
            np.savez_compressed(filename, image)

        pRequest.unlock()

def getIMUValues(sense):
    accel = sense.get_accelerometer_raw()
    gyro = sense.get_gyroscope_raw()
    compass = sense.get_compass_raw()

    return (accel, gyro, compass)

def generateFileName(frame_number, imu_tuple, time, voltage, temperature, pressure):
    accel, gyro, compass = imu_tuple
    return f"{frame_number}_{time:.2f}_{voltage:.2f}_{temperature:.2f}_{pressure:.2f}_{accel['x']:.6f}_{accel['y']:.6f}_{accel['z']:.6f}_{gyro['x']:.6f}_{gyro['y']:.6f}_{gyro['z']:.6f}_{compass['x']:.6f}_{compass['y']:.6f}_{compass['z']:.6f}"
    

frame_number = 0

while(1):
    for v in lens_values:
        o.current(v)
        time.sleep(0.02)
        sense.clear((80, 80, 0))
        imu_values = getIMUValues(sense)
        temp = sense.get_temperature()
        pressure = sense.get_pressure()
        sense.clear((0, 80, 0))
        filename = generateFileName(frame_number, imu_values, time.time(), v, temp, pressure)
        sense.clear((0, 80, 80))
        recordImage(filename)
        sense.clear((0, 0, 80))
        frame_number = frame_number + 1
