import cv2
import socket
import struct

# Create a socket and bind it to a specific IP and port
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ("0.0.0.0", 3000)
server_socket.bind(server_address)

# Start listening for client connections
server_socket.listen(1)

print("Waiting for a client connection...")

# Accept a client connection
client_socket, client_address = server_socket.accept()
print("Client connected:", client_address)

# Create a VideoCapture object to access the Raspberry Pi camera module
cap = cv2.VideoCapture(0)

# Continuously capture frames from the camera and send them to the client
while True:
    ret, frame = cap.read()

    # Resize the frame to reduce data size (adjust as needed)
    resized_frame = cv2.resize(frame, (640, 480))

    # Serialize the frame using OpenCV's imencode function
    _, encoded_frame = cv2.imencode(".jpg", resized_frame)

    # Pack the frame size and the frame data into a message
    message = struct.pack("Q", len(encoded_frame)) + encoded_frame.tobytes()

    try:
        # Send the message through the socket
        client_socket.sendall(message)

    except socket.error as e:
        print(f"Socket error: {str(e)}")
        break

# Release the resources
cap.release()
client_socket.close()
server_socket.close()