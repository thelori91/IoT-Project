import cv2
import socket
import struct

### CREATING SOCKET ###
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ("0.0.0.0", 3000)
server_socket.bind(server_address)

server_socket.listen(1)

print("Waiting for a client connection...")

client_socket, client_address = server_socket.accept()
print("Client connected:", client_address)

### STARTING CAMERA ###
cap = cv2.VideoCapture(0)

### CAPTURING FRAMES ###
while True:
    ret, frame = cap.read()
    resized_frame = cv2.resize(frame, (640, 480))
    
    _, encoded_frame = cv2.imencode(".jpg", resized_frame) # Serialize the frame using OpenCV's imencode function
    
    message = struct.pack("Q", len(encoded_frame)) + encoded_frame.tobytes() # Pack the frame size and the frame data into a message

    try:
        client_socket.sendall(message)

    except socket.error as e:
        print(f"Socket error: {str(e)}")
        break

cap.release()
client_socket.close()
server_socket.close()