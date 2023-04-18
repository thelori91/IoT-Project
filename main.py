import cv2
import cvzone # Package that is usefull because implements face detection, hand tracking, pose estimation etc... At the base there are OpenCV and MediaPipe which are libraries usefull to play with images and videos 
from cvzone.SelfiSegmentationModule import SelfiSegmentation
seg=SelfiSegmentation() # Real time background replacement using cvzone

img=cv2.imread("resources/images/bg1.jpg") # using for reading images from specific a path
img=cv2.resize(img,(840,640)) # i'm using this function to resize the image passed by parameter

cap = cv2.VideoCapture(0) # object that takes as parameter the index of videocamera device and allow user to use camera

global backgroundremoved # used to allow user to remove/restore his background
backgroundremoved = False

while True:
    key = cv2.waitKey(1) # input from keyboard
    ret,frame=cap.read()
    if backgroundremoved == False:
        frame=cv2.resize(frame,(840,640))
        imgout=frame
    else:
        frame=cv2.resize(frame,(840,640))
        imgout=seg.removeBG(frame,img) 
        
    frame=cv2.imshow("Ciak!",imgout)

    if key == ord('q'): # exit
        break
    elif key == ord('r'): # removing background
        print("--- Removing Background ---")
        img=cv2.imread("resources/images/bg1.jpg")
        img=cv2.resize(img,(840,640))
        backgroundremoved = True
    elif key == ord('u'): # restore background
        print("--- Restoring Background ---")
        backgroundremoved = False
    elif key == ord('1'): # select background 1
        print("--- Background 1 ---")
        img=cv2.imread("resources/images/bg1.jpg")
        img=cv2.resize(img,(840,640))
    elif key == ord('2'):  # select background 2
        print("--- Background 2 ---")
        img=cv2.imread("resources/images/bg2.jpg")
        img=cv2.resize(img,(840,640))
    elif key == ord('3'):  # select background 3
        print("--- Background 3 ---")
        img=cv2.imread("resources/images/bg3.jpg")
        img=cv2.resize(img,(840,640))

cap.release()
cv2.destroyAllWindows()