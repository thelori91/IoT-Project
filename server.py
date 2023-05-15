import cv2
import os
from PIL import Image
from flask import Flask, render_template, Response, request, send_file
import fastwsgi
import socket
import struct
import pickle
import cvzone # Package that is usefull because implements face detection, hand tracking, pose estimation etc... At the base there are OpenCV and MediaPipe which are libraries usefull to play with images and videos 
from cvzone.SelfiSegmentationModule import SelfiSegmentation

first_running = True

def reading_images():
    images_dir_path="resources/images/"
    images_entries = os.listdir(images_dir_path)
    images = []
    for filename in images_entries:
        if not filename.startswith('.'):
            item = os.path.join(images_dir_path, filename)
            img = cv2.imread(item)
            images.append(img)
    return images

def reading_videos():
    video_dir_path="resources/videos/"
    video_entries = os.listdir(video_dir_path)
    videos = []
    for filename in video_entries:
        if not filename.startswith('.'):
            item = os.path.join(video_dir_path, filename)
            videos.append(item)
    return videos

try:
    ### INITIALIZATION SET UP VAR ###
    seg = SelfiSegmentation() # Real time background replacement using cvzone

    modality = 'images' 
    opening_video = None
    background = None
    background_removed = False
    
    index_array = 0
    index_video_array = 0
    
    print("*** STARTING SOCKET ***")
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('raspberrypi.local', 2030)) # Change the hostname and port number as needed

    # Create a receive buffer and a variable to track the remaining data to receive
    recv_buffer = b''
    remaining_size = 0
    
    print("*** STARTING READING FROM FILE ***")
    images = reading_images()
    videos = reading_videos()
    
    app = Flask('__name__') # creating a new instance of Flask, __name__ is a special arg which represents name of current module
    #cap = cv2.VideoCapture(0) # object that takes as parameter the index of videocamera device and allow user to use camera

    ### FUNCTION THAT HANDLE THE STREAMING ###
    def video_stream():
        global modality
        global opening_video
    
        global remaining_size
        global recv_buffer
        while True:
            # Receive the data length if we don't have enough data in the receive buffer
            if remaining_size == 0:
                data_size = client_socket.recv(4)
                remaining_size = struct.unpack('!i', data_size)[0]

            # Receive the data itself and append it to the receive buffer
            recv_data = client_socket.recv(remaining_size)
            remaining_size -= len(recv_data)
            recv_buffer += recv_data

            # If we have received a complete frame, decode and display it
            if remaining_size == 0:
                frame = pickle.loads(recv_buffer)
                cv2.waitKey(1)
                recv_buffer = b''
            frame = cv2.resize(frame,(640,480))
            
            if background_removed == True and modality == 'images':
                resized_background = cv2.resize(background, (frame.shape[1], frame.shape[0]))
                imgout = seg.removeBG(frame,resized_background)
            elif background_removed == True and modality == 'videos':
                importVideoFrames, background_v = opening_video.read() 
                if not importVideoFrames:
                        opening_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                resized_background = cv2.resize(background_v, (frame.shape[1], frame.shape[0]))
                imgout = seg.removeBG(frame,resized_background)
            else:
                imgout = frame
            
            hasFrame, buffer = cv2.imencode('.jpg',imgout)
            imgout = buffer.tobytes()
            yield (b' --frame\r\n' b'Content-type: image/jpeg\r\n\r\n' + imgout +b'\r\n')

    ### RENDERS AN HTML PAGE ###
    @app.route('/')
    def index():
        global first_running
        if first_running == False:
            print("*** RELOAD INIT ***")
            global modality
            global opening_video
            global background
            global background_removed
            global index_array
            global index_video_array
            global images
            global videos
            
            modality = 'images' 
            opening_video = None
            background = None
            background_removed = False
        
            index_array = 0
            index_video_array = 0

            print("*** RELOAD READING FROM FILE ***")
            images = reading_images()
            videos = reading_videos()
        first_running = False
        dir_path="resources/images/"
        entries = os.listdir(dir_path)
        image_names = []
        for filename in entries:
            if not filename.startswith('.'):
                image_names.append(filename)
        return render_template('index.html',image_names=image_names)
    
    @app.route('/resources/images/<path:filename>')
    def get_image(filename):
        return send_file(os.path.join(os.getcwd(), 'resources', 'images', filename), mimetype='image/jpeg')

    ### UPDATE MODALITY BY USING BUTTON - ENABLED ###
    @app.route('/update_modality', methods=['POST'])
    def update_modality():

        global modality
        global background
        global opening_video

        data = request.get_json()
        value = data['value']
        if value == 'change' and modality == 'images':
            opening_video = cv2.VideoCapture(videos[index_video_array])
            modality = 'videos'
        elif value == 'change' and modality == 'videos':
            if opening_video.isOpened():
                opening_video.release()
            background = images[index_array]
            modality = 'images'
        print("*** ",modality," ***")
        return 'Value updated successfully!'

    ### SET/RM BACKGROUND BY USING BUTTON - ENABLED ###
    @app.route('/update_background', methods=['POST'])
    def update_background():
        
        global background
        global background_removed
        global index_array

        data = request.get_json()
        value = data['value']
        if value == 'change' and background_removed == True:
            background_removed = False
        elif value == 'change' and background_removed == False:
            background = images[index_array]
            background_removed = True
        return 'Value updated successfully!'
    
    ### UPDATE IMAGES onClick - ENABLED ###
    @app.route('/image_clicked')
    def image_clicked():
        global background
        global images
        global index_array

        index = request.args.get('index')
        index_array = int(index)
        background = images[index_array]
        return 'Value updated successfully!'

    ### UPDATE IMAGES/VIDEOS BY USING BUTTONS - NOT ENABLED ###
    @app.route('/update_value', methods=['POST'])
    def update_value():
        global index_array
        global index_video_array
        global background
        global modality
        global opening_video

        data = request.get_json()
        value = data['value']
        if modality == 'images' and background_removed == True:
            if ((value == 'right') and (index_array < len(images)-1)):
                index_array = index_array+1
            elif ((value == 'right') and (index_array == len(images)-1)):
                index_array = 0
            elif ((value == 'left') and (index_array > 0)):
                index_array = index_array-1
            elif ((value == 'left') and (index_array == 0)):
                index_array = len(images)-1
            background = images[index_array]
        elif modality == 'videos' and background_removed == True:
            if ((value == 'right') and (index_video_array < len(videos)-1)):
                index_video_array = index_video_array+1
            elif ((value == 'right') and (index_video_array == len(videos)-1)):
                index_video_array = 0
            elif ((value == 'left') and (index_video_array > 0)):
                index_video_array = index_video_array-1
            elif ((value == 'left') and (index_video_array == 0)):
                index_video_array = len(videos)-1
            opening_video = cv2.VideoCapture(videos[index_video_array])
        return 'Value updated successfully!'


    @app.route('/video_feed')
    def video_feed():
        print("*** STARTING ***")
        return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

    if __name__=='__main__':
        fastwsgi.run(app, host="0.0.0.0", port=2024)

except KeyboardInterrupt:
    if opening_video.isOpened():
        opening_video.release()
    print("\n*** PROGRAM TERMINATED BY USER ***")