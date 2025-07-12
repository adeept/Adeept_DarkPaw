import cv2
import zmq
import base64
import numpy as np

context = zmq.Context()
footage_socket = context.socket(zmq.PAIR)
footage_socket.bind('tcp://*:5555')
cv2.namedWindow('Stream',flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
cv2.resizeWindow('Stream',width=640,height=480)
font = cv2.FONT_HERSHEY_SIMPLEX

while True:
	frame = footage_socket.recv_string()
	img = base64.b64decode(frame)
	npimg = np.frombuffer(img, dtype=np.uint8)
	source = cv2.imdecode(npimg, 1)
	cv2.imshow("Stream", source)
	cv2.waitKey(1)