from tkinter import *
from tkinter import messagebox 
import time
import picamera

import matplotlib.pyplot as plt

from sensors import Proximity, IMU

def init(data):
    data.maxProx = 4
    data.maxIMU = 2
    data.recording = False
    data.sensors = []
    data.startTime = None

    initProx(data)
    initIMU(data)
    initCamera(data)
    initStartAndStop(data)
    initClassification(data)

def initProx(data):
    Label(data.root, text="Proximity Sensors").grid(row=0, column=0)
    data.numProx = IntVar(data.root)
    data.numProx.set(0)
    OptionMenu(data.root, data.numProx, *range(data.maxProx+1)).grid(row=0, column=1)

def initIMU(data):
    Label(data.root, text="IMU Sensors").grid(row=1, column=0)
    data.numIMU = IntVar(data.root)
    data.numIMU.set(0)
    OptionMenu(data.root, data.numIMU, *range(data.maxIMU+1)).grid(row=1, column=1)

def initCamera(data):
    Label(data.root, text="Camera:").grid(row=2, column=0)
    data.cameraOn = IntVar(data.root)
    data.cameraOn.set(0)
    Radiobutton(data.root, text="On", variable=data.cameraOn, value=1).grid(row=2, column=1)
    Radiobutton(data.root, text="Off", variable=data.cameraOn, value=0).grid(row=3, column=1)

def initStartAndStop(data):
    Button(data.root, text="Start", command= lambda: start(data)).grid(row=4, column=0)
    Button(data.root, text="Stop", command=lambda: stop(data)).grid(row=4, column=1)

def initClassification(data):
    data.activityLabel = Label(data.root, text="Classification:")
    data.activity = StringVar(data.root)
    data.activity.set("nothing")
    data.eatingButton = Radiobutton(data.root, text="Eating", variable=data.activity, value="eating")
    data.talkingButton = Radiobutton(data.root, text="Talking", variable=data.activity, value="talking")
    data.nothingButton = Radiobutton(data.root, text="Nothing", variable=data.activity, value="nothing")

def start(data):
    if validateInput(data):
        data.activityLabel.grid(row=5, column=0)
        data.eatingButton.grid(row=5, column=1, sticky=W)
        data.talkingButton.grid(row=6, column=1, sticky=W)
        data.nothingButton.grid(row=7, column=1, sticky=W)

        if data.cameraOn.get():
            data.camera = picamera.PiCamera()
            data.camera.start_recording('video.h264')

        createSensors(data)
        data.startTime = time.time()
        data.recording = True

def validateInput(data):
    if data.numProx.get() == data.numIMU.get() == data.cameraOn.get() == 0:
        messagebox.showinfo("Error", "Must select at least one sensor")
        return False
    return True

def stop(data):
    data.recording = False

    if data.cameraOn.get():
        data.camera.stop_recording()

    setupPlots(data)
    for sensor in data.sensors:
        sensor.finalPlot()

    data.activityLabel.grid_remove()
    data.eatingButton.grid_remove()
    data.talkingButton.grid_remove()
    data.nothingButton.grid_remove()
    saveData(data)

def createSensors(data):
    data.sensors = []
    numProx = data.numProx.get()
    numIMU = data.numIMU.get()
    for i in range(numProx):
        data.sensors.append(Proximity(i))
    for i in range(numIMU):
        data.sensors.append(IMU(i))

def setupPlots(data):
    plt.figure(1)
    plt.ion()
    numPlots = 0
    for sensor in data.sensors:
        numPlots += sensor.numPlots
    currPlot = 1
    for i in range(1, len(data.sensors)+1):
        sensor = data.sensors[i-1]
        subplot = (numPlots, 1, currPlot)
        sensor.setupPlot(subplot)
        currPlot += sensor.numPlots
    plt.tight_layout()
    plt.show()

def timerFired(data):
    if not data.recording: return
    for sensor in data.sensors:
        sensor.read(time.time() - data.startTime, data.activity.get())

def saveData(data):
    for sensor in data.sensors:
        sensor.writeData()

def run():
    class Struct(object): pass
    data = Struct()
    data.root = Tk()
    init(data)
    data.timerDelay = 10

    def timerFiredWrapper(data):
        timerFired(data)
        # pause, then call timerFired again
        data.root.after(data.timerDelay, timerFiredWrapper, data)
    timerFiredWrapper(data)
    
    data.root.mainloop() 

run()
