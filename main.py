import cv2
import cvzone
from cvzone.SelfiSegmentationModule import SelfiSegmentation
seg=SelfiSegmentation()

img=cv2.imread("resources/images/bg1.jpg")
img=cv2.resize(img,(840,640))

cap = cv2.VideoCapture(0)
global backgroundremoved
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

    if key == ord('q'): 
        break
    elif key == ord('r'): 
        print("--- Removing Background ---")
        img=cv2.imread("resources/images/bg1.jpg")
        img=cv2.resize(img,(840,640))
        backgroundremoved = True
    elif key == ord('u'): # undo
        print("--- Restoring Background ---")
        backgroundremoved = False
    elif key == ord('1'): 
        print("--- Background 1 ---")
        img=cv2.imread("resources/images/bg1.jpg")
        img=cv2.resize(img,(840,640))
    elif key == ord('2'): 
        print("--- Background 2 ---")
        img=cv2.imread("resources/images/bg2.jpg")
        img=cv2.resize(img,(840,640))
    elif key == ord('3'): 
        print("--- Background 3 ---")
        img=cv2.imread("resources/images/bg3.jpg")
        img=cv2.resize(img,(840,640))

cap.release()
cv2.destroyAllWindows()