#!/usr/bin/env python3
import cv2
import numpy as np
import pyboof as pb
from QRCscan import QRCscanner
import time

detector = QRCscanner()

def resize_img(img, scale_percent):
   width = int(img.shape[1]*scale_percent/100)
   height = int(img.shape[0]*scale_percent/100)
   dim = (width, height)

   resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
   return resized

cap = cv2.VideoCapture(0)
cap.set(3, 800)
cap.set(4, 600)
if not cap.isOpened():
   print("Cannot open camera")
   exit()

#pb.init_memmap()

# Detects all the QR Codes in the image and prints their message and location
#data_path = "../data/example/fiducial/qrcode/image03.jpg"
#data_path = "../data/example/fiducial/qrcode/test1.jpg"

#detector = pb.FactoryFiducial(np.uint8).qrcode()

#image = pb.load_single_band(data_path, np.uint8)

#image = cv2.imread(data_path, cv2.IMREAD_COLOR)
#image = cv2.imread(data_path, cv2.COLOR_BGR2GRAY)
t0 = 0
t1 = 0
n_frames = 0
fps = 0
print("Press q to stop capturing")
while True:
   ret, frame = cap.read()
   if not ret:
      print("Can't receive frame")
      break
   _, _, result, status, _ = detector.process_frame(frame)
   
   if not n_frames%10:
       t1 = time.time()
       fps = int(n_frames/(t1-t0))
       t0 = t1
       n_frames = 0
   n_frames+=1
   result = cv2.putText(result, "FPS: {0}".format(fps), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 100), 2)  
   cv2.imshow("Results", result)
   if cv2.waitKey(1)==ord('q'):
      break

cap.release()
