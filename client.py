import cv2
import os
import fastwsgi
import socket
import struct
import numpy as np
import cvzone # Package that is usefull because implements face detection, hand tracking, pose estimation etc... At the base there are OpenCV and MediaPipe which are libraries usefull to play with images and videos 
from flask import Flask, render_template, Response, request, send_file
from cvzone.SelfiSegmentationModule import SelfiSegmentation

first_running = True
socket_server_ip = "raspberrypi.local"
socket_server_port = 3000

def reading_images():
    images_dir_path="resources/images/"
    images_entries = sorted(os.listdir(images_dir_path))
    images = []
    valid_extensions = ['.jpeg', '.jpg', '.png']
    for filename in images_entries:
        file_extension = os.path.splitext(filename)[1]
        if not filename.startswith('.') and file_extension.lower() in valid_extensions:
            item = os.path.join(images_dir_path, filename)
            img = cv2.imread(item)
            images.append(img)
    return images

def reading_videos():
    video_dir_path="resources/videos/"
    video_entries = sorted(os.listdir(video_dir_path))
    videos = []
    valid_extensions = ['.mp4', '.avi', '.mkv'] 
    for filename in video_entries:
        file_extension = os.path.splitext(filename)[1]
        if not filename.startswith('.') and file_extension.lower() in valid_extensions :
            item = os.path.join(video_dir_path, filename)
            videos.append(item)
    return videos

try:
    ### INITIALIZATION & SETUP VAR ###
    seg = SelfiSegmentation() # Real time background replacement using cvzone

    modality = "images" 
    opening_video = None
    background = None
    background_removed = False
    
    index_array = 0
    index_video_array = 0
    
    print("*** STARTING SOCKET ***")
    
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (socket_server_ip, socket_server_port) 
    client_socket.connect(server_address)
    
    print("*** STARTING READING FROM FILE ***")
    images = reading_images()
    videos = reading_videos()
    
    app = Flask('__name__') # creating a new instance of Flask, __name__ is a special arg which represents name of current module

    ### FUNCTION THAT HANDLE THE STREAMING ###
    def video_stream():
        global modality
        global opening_video
    
        while True:
            try:
                header = client_socket.recv(8) # Receive the message header containing the frame size
                if len(header) == 0:
                    break

                frame_size = struct.unpack("Q", header)[0] # Unpack the frame size from the header

                frame_data = b"" # Receive the frame data, using b to use frame_data as bytes string, not unicode
                while len(frame_data) < frame_size:
                    remaining_bytes = frame_size - len(frame_data)
                    frame_data += client_socket.recv(remaining_bytes)

                frame_array = np.frombuffer(frame_data, dtype=np.uint8) # Convert the frame data to a NumPy array

                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR) # Decode the frame and display it
            except socket.error as e:
                print(f"Socket error: {str(e)}")
                break

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
            imgout = buffer.tobytes() # converted to use below
            yield (b' --frame\r\n' b'Content-type: image/jpeg\r\n\r\n' + imgout +b'\r\n') # generating seq of frames

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
        extract_frames("resources/videos/support")
        image_name = reading_dir("resources/images/")
        video_name = reading_dir("resources/videos/support")
        return render_template('index.html', image_names = image_name, video_names = video_name)
    
    ### FUNCTION USED TO EXTRACT FRAME FROM A VIDEO ###
    def extract_frames(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        videos_name = reading_videos()
        for filename in videos_name:
            cap = cv2.VideoCapture(filename)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
            success, frame = cap.read()
            if success:
                video_name = os.path.splitext(os.path.basename(filename))[0]
                frame_name = f"{video_name}.jpg"
                frame_path = os.path.join(output_dir, frame_name)
                cv2.imwrite(frame_path, frame)
        print("*** ALL FRAMES ARE SUCCESSFULLY SAVED ***")       
        cap.release()        

    ### USED TO EXTRACT NAME OF FILES INSIDE A DIR ###
    def reading_dir(path):
        entries = sorted(os.listdir(path))
        names = []
        for filename in entries:
            if not filename.startswith('.'):
                names.append(filename)
        return names

    @app.route('/resources/images/<path:filename>')
    def get_image(filename):
        return send_file(os.path.join(os.getcwd(), 'resources', 'images', filename), mimetype='image/jpeg')

    @app.route('/resources/videos/support/<path:filename>')
    def get_video(filename):
        return send_file(os.path.join(os.getcwd(), 'resources', 'videos', 'support', filename), mimetype='image/jpeg')

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
    
    @app.route('/video_clicked')
    def video_clicked():
        global background
        global opening_video
        global index_video_array

        index = request.args.get('index')
        index_video_array = int(index)
        opening_video = cv2.VideoCapture(videos[index_video_array])
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
    client_socket.close()
    print("\n*** PROGRAM TERMINATED BY USER ***")