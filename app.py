import cv2
import time
from PIL import Image
from flask import Flask, render_template, Response, request
try:
    ### INITIALIZATION STEP ###
    initTime = time.time()
    background = None
    index_array = 0
    image_files = ["resources/images/default.jpg", "resources/images/bg1.jpg", "resources/images/bg2.jpg", "resources/images/bg3.jpg"]
    # Load all images into a list
    images = []
    for filename in image_files:
        img = cv2.imread(filename)
        images.append(img)

    app = Flask('__name__') # creating a new instance of Flask, __name__ is a special arg which represents name of current module
    cap = cv2.VideoCapture(0)
    oceanVideo = cv2.VideoCapture("resources/videos/ocean.mp4")
    ### FUNCTION THAT HANDLE THE STREAMING ###
    def video_stream():
        global background
        global calibrateFlag
        background = cv2.imread("resources/images/default.jpg")
        bgSubtractor = cv2.bgsegm.createBackgroundSubtractorMOG() # Lib that improved Background-Foreground Segmentation using Gaussian Mixture-based
        calibrateFlag = False
        initTime = time.time() # Starting time
        calibratingText = "Learning background..."
        calibratingTextsize = cv2.getTextSize(calibratingText, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0] # Calculate the size of Text

        while True:
            hasFrame, frame = cap.read() 
            importVideoFrames, bg = oceanVideo.read()  
            if not hasFrame:
                break
            else:
                if calibrateFlag == False: # Function that learn the background 
                    bgSubtractor.apply(frame, learningRate=0.5) # Here from frame i will learn with a learningRate 0.5 which the value between 0 and 1 that indicates how fast the background model is learnt
                                                                # I'm apply to the bgSubtractor, which implies the learning
                    
                    calibratingTextX = int((frame.shape[1] - calibratingTextsize[0]) / 2) # Height of Frame
                    calibratingTextY = int((frame.shape[0] + calibratingTextsize[1]) / 2) # Width of Frame
                    cv2.putText(frame, calibratingText, (calibratingTextX, calibratingTextY), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                    timeStr = "Time elapsed: {:.1f} s".format(time.time() - initTime)
                    timeTextsize = cv2.getTextSize(timeStr, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                    timeTextX = int(frame.shape[1] - timeTextsize[0])
                    timeTextY = int(frame.shape[0] - timeTextsize[1])
                    cv2.putText(frame, timeStr, (timeTextX, timeTextY), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    fgMask = bgSubtractor.apply(frame, learningRate=0) # Here, without learning, I'm saving the 'Foreground'
                    img_fg = cv2.bitwise_and(frame, frame, mask = fgMask) # Operation that do the operation ad between the two images, which are frame, using as a mask the foreground

                    mask_inv = cv2.bitwise_not(fgMask) # calculating the inverse of fgMask
                    if not importVideoFrames:
                        oceanVideo.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    resized_background = cv2.resize(bg, (img_fg.shape[1], img_fg.shape[0]))
                    
                    background_masked = cv2.bitwise_and(resized_background, resized_background, mask=mask_inv) # Use the inverted mask to extract the background from the background image
                    
                    #result = cv2.add(img_fg, background_masked)# Combine the person and background images
                    frame = cv2.add(img_fg, background_masked)# Combine the person and background images
                    #cv2.imshow('Ciak!', result)
                hasFrame, buffer = cv2.imencode('.jpg',frame)
                frame = buffer.tobytes()
                yield (b' --frame\r\n' b'Content-type: image/jpeg\r\n\r\n' + frame +b'\r\n')
            calibrateFlag = True if (time.time() - initTime > 7) else False

    ## Renders an HTML page##
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/update_value', methods=['POST'])
    def update_value():
        global calibrateFlag
        global index_array
        if calibrateFlag == True:
            global value
            global background
            data = request.get_json()
            value = data['value']
            print("BEFORE INC index",index_array)
            if ((value == 'right') and (index_array < len(images)-1)):
                index_array = index_array+1
            elif ((value == 'right') and (index_array == len(images)-1)):
                index_array = 0
            elif ((value == 'left') and (index_array > 0)):
                index_array = index_array-1
            elif ((value == 'left') and (index_array == 0)):
                index_array = len(images)-1
            print("AFTER INC index",index_array)
            background = images[index_array]

        return 'Value updated successfully!'
    
    @app.route('/video_feed')
    def video_feed():
        return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

    if __name__=='__main__':
        from waitress import serve #Waitress is a pure Python WSGI server, I'm using this because without i can use a dev server, which is not used in production
        serve(app, host="0.0.0.0", port=2024)

except KeyboardInterrupt:
    if cap.isOpened():
        cap.release()
    print("\n*** Program terminated by user. ***")