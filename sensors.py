import Adafruit_ADS1x15
import math
import matplotlib.pyplot as plt
import RTIMU
import statistics
import random

def writeFile(path, contents):
    with open(path, 'wt') as f: f.write(contents)

def normalizeData(dataPoints):
    maxPoint = max(dataPoints)
    minPoint = min(dataPoints)
    #normalize points to (0, 2) range
    normalizedPoints = list(map(
        lambda x: 2*(x - minPoint)/(maxPoint - minPoint),
        dataPoints))
    #shift the points so the range is (-1, 1)
    shiftedPoints = list(map(lambda x: x - 1, normalizedPoints))
    return shiftedPoints
    

#Generic Sensor class that records and plots a single data stream
class Sensor(object):
    def __init__(self, name, ylabel):
        self.name = name
        self.ylabel = ylabel
        self.xlabel = "Time"
        self.data = []
        self.time = []
        self.category = []
        self.subplot = None
        self.numPlots = 1

    def addPoint(self, timeStamp, dataValue, category):
        self.time.append(timeStamp)
        self.data.append(dataValue)
        self.category.append(category)

    def createSubplot(self, title, subplot):
        plt.subplot(*subplot)
        plt.title(self.name + " " + title)
        plt.ylabel(self.ylabel)
        plt.xlabel(self.xlabel)

    def setupPlot(self, subplot):
        self.subplot = subplot
        plt.subplot(*self.subplot)
        plt.title(self.name)
        plt.ylabel(self.ylabel)
        plt.xlabel(self.xlabel)

    def finalPlot(self):
        plt.subplot(*self.subplot)
        normalizedData = normalizeData(self.data)
        plt.plot(self.time, normalizedData)

        self.markCategories()

    # mark the regions where each activity occurred
    def markCategories(self):
        (numSensors, _, index) = self.subplot
        lastChangeTime = 0
        for i in range(1, len(self.category)):
            currCategory = self.category[i]
            if currCategory != self.category[i-1]:
                #have a new category so plot a line here
                lastCategory = self.category[i-1]
                if lastCategory == 'nothing': color = 'b'
                elif lastCategory == 'talking': color = 'r'
                else: color = 'g'
                for plot in range(self.numPlots):
                    plt.subplot(numSensors, 1, index+plot)
                    plt.axvspan(lastChangeTime, self.time[i], color=color, alpha=0.3)
                lastChangeTime = self.time[i]
        if self.category[-1] == 'nothing': color = 'b'
        elif self.category[-1] == 'talking': color = 'r'
        else: color = 'g'
        for plot in range(self.numPlots):
            plt.subplot(numSensors, 1, index+plot)
            plt.axvspan(lastChangeTime, self.time[-1], color=color, alpha=0.3)

    def writeData(self):
        contents = 'Time,Label,Data\n'
        for i in range(len(self.data)):
            contents += '%f,%s,%f\n' % (self.time[i], self.category[i], self.data[i])
        writeFile('%s.csv' % (self.name), contents)

#Adafruit ADS1115 Proximity Sensor
class Proximity(Sensor):
    adc = Adafruit_ADS1x15.ADS1115()

    def __init__(self, index=0):
        self.index = index
        super().__init__('Proximity %d' % index, '')

    def read(self, time, category):
        proxVal = Proximity.adc.read_adc(self.index, gain=1)
        self.addPoint(time, proxVal, category)

#MPU-9250 IMU Sensor
class IMU(Sensor):
    def __init__(self, index=0):
        self.index = index
        super().__init__("IMU %d" % self.index, "")
        self.numPlots = 3
        self.roll = [] 
        self.pitch = [] 
        self.yaw = []
        self.roll_rate = []
        self.pitch_rate = []
        self.yaw_rate = []

        #IMU 0 is at address 0x68
        #IMU 1 is at address 0x69, and should have AD0/SD0 connected to high
        self.settings_file = "RTIMULib%d" % self.index
        self.s = RTIMU.Settings(self.settings_file)
        self.imu = RTIMU.RTIMU(self.s)
        if self.imu.IMUInit():
            self.imu.setSlerpPower(0.02)
            self.imu.setGyroEnable(True)
            self.imu.setAccelEnable(True)
            self.imu.setCompassEnable(True)
        else:
            raise Exception("IMU unable to initialize")

    def setupPlot(self, subplot):
        (numSensors, _, i) = subplot
        self.subplot = subplot
        self.createSubplot("Roll", (numSensors, 1, i))
        self.createSubplot("Pitch", (numSensors, 1, i+1))
        self.createSubplot("Yaw", (numSensors, 1, i+2))
        
    def addPoint(self, timeStamp, roll, pitch, yaw, roll_rate, pitch_rate, yaw_rate, category):
        self.roll.append(roll)
        self.pitch.append(pitch)
        self.yaw.append(yaw)
        self.roll_rate.append(roll_rate)
        self.pitch_rate.append(pitch_rate)
        self.yaw_rate.append(yaw_rate)
        self.time.append(timeStamp)
        self.category.append(category)
        
    def read(self, time, category):
        if self.imu.IMURead():
            imuData = self.imu.getIMUData()
            fusionPose = imuData['fusionPose']
            gyro = imuData['gyro']
            roll=(round(math.degrees(fusionPose[0]), 1))
            pitch=(round(math.degrees(fusionPose[1]), 1))
            yaw=(round(math.degrees(fusionPose[2]), 1))
            roll_rate=(round(math.degrees(gyro[0]), 1))
            pitch_rate=(round(math.degrees(gyro[1]), 1))
            yaw_rate=(round(math.degrees(gyro[2]), 1))
            self.addPoint(time, roll, pitch, yaw, roll_rate, pitch_rate, yaw_rate, category)
        
    def writeData(self):
        contents = 'Time,Label,Roll,Pitch,Yaw,Roll Rate,Pitch Rate,Yaw Rate\n'
        for i in range(len(self.time)):
            contents += '%f,%s,%f,%f,%f,%f,%f,%f\n' % (self.time[i], self.category[i],
                         self.roll[i], self.pitch[i], self.yaw[i], self.roll_rate[i],
                         self.pitch_rate[i], self.yaw_rate[i])
        writeFile('%s.csv' % self.name, contents)

    def finalPlot(self):
        (numSensors, _, i) = self.subplot
        plt.subplot(numSensors, 1, i)
        normalizedRoll = normalizeData(self.roll)
        plt.plot(self.time, normalizedRoll)
        plt.subplot(numSensors, 1, i+1)
        normalizedPitch = normalizeData(self.pitch)
        plt.plot(self.time, normalizedPitch)
        plt.subplot(numSensors, 1, i+2)
        normalizedYaw = normalizeData(self.yaw)
        plt.plot(self.time, normalizedYaw)
        
        self.markCategories()
