import PIL
from PIL import Image,ImageTk
import cv2
from tkinter import *
import numpy as np
import threading
from pynput.mouse import Controller
from pynput.mouse import Button as mButton

class CameraInterface:
    def __init__(self):
        self.lowerBound = np.array([29, 86, 6])
        self.upperBound = np.array([64, 255, 255])

        self.cam = cv2.VideoCapture(0)
        ret, self.img = self.cam.read()

        self.root = Tk()
        self.root.bind('<Escape>', lambda e: self.root.quit())
        # self.root.bind("a", lambda x: self.pauseLoop())

        self.kernelOpen = np.ones((5, 5))
        self.kernelClose = np.ones((20, 20))

        self.font = cv2.FONT_HERSHEY_SIMPLEX

        self.varMouse = IntVar()
        self.varClick = IntVar()

        self.lmain = Label(self.root)

        self.red = Button(self.root, text="red", bg="red", command=self.detectRed)
        self.green = Button(self.root, text="green", command=self.detectGreen, bg="green")
        self.blue = Button(self.root, text="blue", command=self.detectBlue, bg="blue")
        # self.rgbContainer = Label(self.root, text="test")
        self.mouseCheckbox = Checkbutton(self.root, text="control mouse?", variable=self.varMouse, command=self.mouseMovement)
        self.clickCheckbox = Checkbutton(self.root, text="control with click?", variable=self.varClick, command=self.clickControl)

        # self.startCam = Button(self.root, text="start camera", command=self.startThread)

        self.lmain.grid(row=0, column=0, columnspan=2)
        self.red.grid(row=1, column=0, sticky='nesw')
        self.green.grid(row=2, column=0, sticky='nesw')
        self.blue.grid(row=3, column=0, sticky='nesw')
        # self.rgbContainer.grid(row=1, column=1, rowspan=3, sticky='nesw')

        self.mouseCheckbox.grid(row=1, column=1,  sticky='nesw')
        self.clickCheckbox.grid(row=2, column=1,  sticky='nesw')

        # self.startCam.grid(row=4, column=0, columnspan=3)

        self.mouse = Controller()

        self.screenx = self.root.winfo_screenwidth()
        self.screeny = self.root.winfo_screenheight()

        self.camx = 340
        self.camy = 220

        self.mouseOn = False
        self.clickControlOn = False

        self.pinchFlag = True

    def detectRed(self):
        self.lowerBound = np.array([170, 120, 150])
        self.upperBound = np.array([190, 255, 255])

    def detectGreen(self):
        self.lowerBound = np.array([29, 86, 6])
        self.upperBound = np.array([64, 255, 255])

    def detectBlue(self):
        self.lowerBound = np.array([110, 150, 100])
        self.upperBound = np.array([120, 255, 255])

    def startThread(self):
        threadCam = threading.Thread(target=self.show_frame)
        threadCam.start()

    def doAction(self):
        print("do action")

    def mouseMovement(self):
        if self.varMouse.get():
            print("mouseOn")
            self.mouseOn = True
        else:
            print("mouseOff")
            self.mouseOn = False

    def clickControl(self):
        if self.varClick.get():
            print("click control on")
            self.clickControlOn = True
        else:
            print("click control off")
            self.clickControlOn = False

    def nothing(self):
        pass

    def create_trackbar(self):

        # set trackbar
        hh = 'hue high'
        hl = 'hue low'
        sh = 'saturation high'
        sl = 'saturation low'
        vh = 'value high'
        vl = 'value low'
        thv = 'th1'

        # set ranges
        cv2.createTrackbar(hh, "color_hsv", self.upperBound[0], 179, self.nothing)
        cv2.createTrackbar(hl, "color_hsv", self.lowerBound[0], 179, self.nothing)
        cv2.createTrackbar(sh, "color_hsv", self.upperBound[1], 255, self.nothing)
        cv2.createTrackbar(sl, "color_hsv", self.lowerBound[1], 255, self.nothing)
        cv2.createTrackbar(vh, "color_hsv", self.upperBound[2], 255, self.nothing)
        cv2.createTrackbar(vl, "color_hsv", self.lowerBound[2], 255, self.nothing)
        cv2.createTrackbar(thv, "color_hsv", 127, 255, self.nothing)

    def click(self, pinchFlag, conts):
        '''
        Performs a click based on the pinchFlag and use the image´s countours
        to define a new rectangle
        Args:
            pinchFlag Flag to controls the clicks
            conts Countours of the image
        Returns:
            mouseLoc Mouse coordinates location
            pinchFlag Flag to controls the clicks
        '''
        print("click!")
        x, y, w, h = cv2.boundingRect(conts[0])
        # drawing the rectangle
        cv2.rectangle(self.img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cx = int(x + w / 2)
        cy = int(y + h / 2)
        cv2.circle(self.img, (cx, cy), int((w + h) / 4), (0, 0, 255), 2)

        if not pinchFlag:  # perform only if pinch is off
            pinchFlag = True  # setting pinch flag on
            self.mouse.press(mButton.left)

        mouseLoc = (self.screenx - (cx * self.screenx / self.camx), cy * self.screeny / self.camy)
        return mouseLoc, pinchFlag

    def show_frame(self):

        ret, self.img = self.cam.read()

        # flipping for the selfie cam right now to keep sane

        self.img = cv2.flip(self.img, 1)
        self.img = cv2.resize(self.img, (self.camx, self.camy))

        # convert BGR to HSV
        frame = cv2.cvtColor(self.img, cv2.COLOR_RGB2BGR)
        imgHSV = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        # create the Mask
        mask = cv2.inRange(imgHSV, self.lowerBound, self.upperBound)
        # morphology
        maskOpen = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernelOpen)
        maskClose = cv2.morphologyEx(maskOpen, cv2.MORPH_CLOSE, self.kernelClose)

        maskFinal = maskClose
        conts, h = cv2.findContours(maskFinal.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        n_objects = len(conts)

        cv2.drawContours(frame, conts, -1, (255, 0, 0), 3)

        if conts:
            x, y, w, h = cv2.boundingRect(conts[0])
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            x1, y1, w1, h1 = cv2.boundingRect(conts[0])
            x1 = int(x1 + w1 / 2)
            y1 = int(y1 + h1 / 2)
            cv2.circle(frame, (x1, y1), 2, (0, 0, 255), 2)

            if self.mouseOn:

                if (self.pinchFlag):  # perform only if pinch is on
                    self.pinchFlag = False
                    self.mouse.release(mButton.left)

                # Compute mouse location
                mouseLoc = (self.screenx - (x1 * self.screenx / self.camx), y1 * self.screeny / self.camy)
                # mouse.position = mouseLoc

                # If there is only one object, it means both finger
                # (objects) collided so a click take place
                if n_objects == 1:
                    print("click")
                    mouseLoc, pinchFlag = self.click(self.pinchFlag, conts)

                self.mouse.position = mouseLoc

            # TO BE IMPLEMENTED
            if self.clickControlOn:
                print("click control on")

        imgPIL = PIL.Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=imgPIL)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(10, self.show_frame)


if __name__ == "__main__":

    camInt = CameraInterface()
    camInt.show_frame()
    camInt.root.mainloop()