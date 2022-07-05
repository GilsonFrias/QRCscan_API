#!/usr/bin/env python3
import cv2
import numpy as np
import pyboof as pb
from core.camera.QRCscan import QRCscanner
import time

detector = QRCscanner()

def resize_img(img, scale_percent):
   width = int(img.shape[1]*scale_percent/100)
   height = int(img.shape[0]*scale_percent/100)
   dim = (width, height)

   resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
   return resized

cap = cv2.VideoCapture(0)
cap.set(3, 800) #It seams that the rotable cam only supports 640x480
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
not_in_color = (0, 0, 255)
in_color = (0, 255, 0)
in_txt = 'Vehiculo en zona de carga'
not_in_txt = 'Sin vehiculo en zona de carga'
_data = ''
print("Press q to stop capturing")
while True:
   ret, frame = cap.read()
   if not ret:
      print("Can't receive frame")
      break
   try:
      data, bboxes, result, _, _ = detector.process_frame(frame)
   except ValueError:
      print("Error: could not unpack return values from QRCscan.process_frame")
      continue
   msg = not_in_txt
   col = not_in_color
   if len(bboxes)>0:
      _data = data[0]
      #print(data)
      #print(len(bboxes))
      #print(bboxes[0][0])
      vertex0 = bboxes[0][0]
      vertex1 = bboxes[0][1]
      vertex2 = bboxes[0][2]
      vertex3 = bboxes[0][3]
      #print('vertex0', vertex0)
      #print('vertex1', vertex1)
      #print('bound', int(result.shape[0]*0.3))
      if (vertex0[1] > int(result.shape[0]*0.30)) and (vertex1[1] > int(result.shape[0]*0.30)):
         msg = ''.join([in_txt, ' con id: ', _data])
         col = in_color
      #result = cv2.circle(result, vertex0, 8, (100, 75, 80), -1)
      #result = cv2.circle(result, vertex1, 8, (100, 75, 80), -1)
      #result = cv2.circle(result, vertex2, 8, (100, 75, 80), -1)
      #result = cv2.circle(result, vertex3, 8, (100, 75, 80), -1)
   #Calculate loading area in result frame
   p0 = (30, result.shape[0]-30)    
   p1 = (result.shape[1]-30, int(result.shape[0]*0.30))
   result = cv2.rectangle(result, p0, p1, col, 3)
   result = cv2.putText(result, msg, (p0[0]+50, p0[1]-40), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)  
   if not n_frames%10:
       t1 = time.time()
       fps = int(n_frames/(t1-t0))
       t0 = t1
       n_frames = 0
   n_frames+=1
   result = cv2.putText(result, "FPS: {0}".format(fps), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1)  
   cv2.imshow("Results", result)
   if cv2.waitKey(1)==ord('q'):
      break

cap.release()
