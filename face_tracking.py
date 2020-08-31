from PyQt5 import QtCore
from pca9685 import *
import cv2
import numpy as np

class MyThreadCV(QtCore.QThread):
    """
    Класс создает и отправляет сигнал
    о центре квадрата,попутно управляя серводвигателями 
    в соответствии с положением центра на осях "x" и "y".
    """
    mysignalCV = QtCore.pyqtSignal(str)

    def __init__(self, cam, queue, width, height, fps, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.cam = cam
        self.queue = queue
        self.width = width
        self.height = height
        self.fps = fps
        self.servo = PCA9685()
        self.test_channel_3 = 3
        self.test_channel_4 = 4
        self.test_channel_11 = 11

        # установки каналов серв на контроллере PCA9685
        self.servo.servos[self.test_channel_3].set(signed=False, reverse=False, min=120, max=120, trim=0,
                                                   exp=0)   # Голова лево-право
        self.servo.servos[self.test_channel_4].set(signed=False, reverse=True, min=120, max=120, trim=0,
                                                   exp=0)   # Голова левый рычаг вверх-вниз
        self.servo.servos[self.test_channel_11].set(signed=False, reverse=False, min=120, max=120, trim=0,
                                                    exp=0)  # Голова правый рычаг вверх-вниз

        # установки стартовых позиций серв
        self.servo.setServo(self.test_channel_3, 50)
        self.servo.setServo(self.test_channel_4, 50)
        self.servo.setServo(self.test_channel_11, 50)

    def run(self):
        try:
            global runningCV
            runningCV = True
            self.capture = cv2.VideoCapture(self.cam)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            self.faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
            while runningCV:
                frame = {}                              # словарь для стрима изображений 
                self.capture.grab()
                retval, img = self.capture.retrieve(0)
                img = cv2.flip(img, 1)
                frame["img"] = img

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = self.faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.2,
                    minNeighbors=5,
                    minSize=(20, 20)
                )
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)
                    xx = int(x + (x + h)) / 2
                    yy = int(y + (y + w)) / 2
                    center = (int(xx), int(yy))

                    self.servo.setServo(self.test_channel_3, (xx / 2))
                    self.servo.setServo(self.test_channel_4, (yy / 2))
                    self.servo.setServo(self.test_channel_11, (yy / 2))

                    s = "Center of Face is:                  " + str(center)
                    self.mysignalCV.emit("%s" % s)
                self.queue.put(frame)
            self.capture.release()

        except cv2.error:
            massage_err = "Camera is not connected!\n" + \
                         "Please push STOP OPEN_CV MODE.\n" +\
                         "Insert WEB camera in USB port.\n" + \
                         "And press START OPEN_CV MODE.\n"
            self.mysignalCV.emit(massage_err)
