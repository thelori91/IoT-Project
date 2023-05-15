import cv2
import socket
import struct
import pickle

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 2030)) # Change the IP address and port number a>
server_socket.listen(0)

# Accept a single connection
connection, addr = server_socket.accept()

# Create a capture object to read from the Raspberry Pi's camera
cap = cv2.VideoCapture(0)

# Set the video size and frame rate
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 30)

# Start capturing frames
while True:
    # Read a frame from the camera
    ret, frame = cap.read()

    # Serialize the frame to a string
    data = pickle.dumps(frame)

    # Pack the data length as a 4-byte integer
    data_size = struct.pack('!i', len(data))

    # Send the data length and data itself over the network
    connection.sendall(data_size)
    connection.sendall(data)