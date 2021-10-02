#!/usr/bin/env python3
import cv2
import numpy as np
import pyboof as pb
from core.camera.QRCscan import QRCscanner
import time
import datetime

#Instantiate detector object
detector = QRCscanner()

def time_convert(sec):
   mins = sec//60
   sec = sec % 60
   hours = mins // 60
   mins = mins % 60
   return "t-carga: {0}:{1}:{2}".format(int(hours), int(mins), int(sec))

def resize_img(img, scale_percent):
   '''
   Image resizing function. scale_percent denotes the percentual factor
   of shrinking or expansion
   '''
   width = int(img.shape[1]*scale_percent/100)
   height = int(img.shape[0]*scale_percent/100)
   dim = (width, height)

   resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
   return resized

#Frame resolution
W = 800
H = 600

#Setup capture devices
cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(2)
cap1.set(3, W) 
cap1.set(4, H)
cap2.set(3, W) #It seams that the rotable cam only supports 640x480
cap2.set(4, H)

if not cap1.isOpened():
   print("Cannot open camera")
   exit()

#Timing variables
t0 = 0
t1 = 0
n_frames = 0
fps = 0

#Color constants
not_in_color = (0, 0, 255)
in_color = (0, 255, 0)
in_txt = 'Cargando: '
not_in_txt = 'Zona de carga libre'
_data = ''
print("Press q to stop capturing")

#Spatial *y* threshold for detection as a percentage of the frame height (measured top to bottom)
detect_th = 0.3

#Chrono variable
t_load1 = 0
t_load2 = 0
t0_load1 = 0
t0_load2 = 0

while True:
   ret1, frame1 = cap1.read()
   ret2, frame2 = cap2.read()
   if not ret1 or not ret2:
      print("Can't receive frame")
      break
   #Detect QR codes
   try:
      data1, bboxes1, result1, _, _ = detector.process_frame(frame1)
      data2, bboxes2, result2, _, _ = detector.process_frame(frame2)
   except ValueError:
      print("Error: could not unpack return values from QRCscan.process_frame")
      continue
   msg = not_in_txt
   col = not_in_color
   #Process frame1
   if len(bboxes1)>0:
      _data = data1[0]
      vertex0 = bboxes1[0][0]
      vertex1 = bboxes1[0][1]
      vertex2 = bboxes1[0][2]
      vertex3 = bboxes1[0][3]
      if (vertex0[1] > int(result1.shape[0]*detect_th)) and (vertex1[1] > int(result1.shape[0]*detect_th)):
         msg = ''.join([in_txt, _data])
         col = in_color
         if t0_load1 == 0:
            t0_load1 = time.time()
         t_load1 = time.time()
      else:
         t0_load1 = 0
         t_load1 = 0
   #Draw loading area1 in result frame
   #p0 = (30, result1.shape[0]-30)    
   #p1 = (result1.shape[1]-30, int(result1.shape[0]*0.30))
   points = [[int(result1.shape[1]/2)-80, int(result1.shape[0]*0.3)], 
            [30, result1.shape[0]-30], [result1.shape[1]-30, result1.shape[0]-30],
            [int(result1.shape[1]/2+80), int(result1.shape[0]*0.3)]]
   #points_th = [[int(result1.shape[1]/2)-168, int(result1.shape[0]*detect_th)], 
   #         [30, result1.shape[0]-30], [result1.shape[1]-30, result1.shape[0]-30],
   #         [int(result1.shape[1]/2+168), int(result1.shape[0]*detect_th)]]
   p0 = (30, result1.shape[0]-30)    
   p1 = (result1.shape[1]-30, int(result1.shape[0]*0.30))
   #result1 = cv2.rectangle(result1, p0, p1, col, 3)
   isClosed = True
   result1 = cv2.polylines(result1, [np.array(points)], isClosed, col, 3)
   #result1 = cv2.fillPoly(result1, [np.array(points_th)], (200, 200, 100), lineType=cv2.LINE_AA)
   result1 = cv2.putText(result1, msg, (p0[0]+50, p0[1]-40), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)  
   t_text = time_convert(t_load1-t0_load1)
   result1 = cv2.putText(result1, t_text, (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 3)  
   msg = not_in_txt
   col = not_in_color
   #Process frame2
   if len(bboxes2)>0:
      _data = data2[0]
      vertex0 = bboxes2[0][0]
      vertex1 = bboxes2[0][1]
      vertex2 = bboxes2[0][2]
      vertex3 = bboxes2[0][3]
      if (vertex0[1] > int(result2.shape[0]*detect_th)) and (vertex1[1] > int(result2.shape[0]*detect_th)):
         msg = ''.join([in_txt, _data])
         col = in_color
         if t0_load2 == 0:
            t0_load2 = time.time()
         t_load2 = time.time()
      else:
         t0_load2 = 0
         t_load2 = 0
   #Draw loading area1 in result frame
   points = [[int(result2.shape[1]/2)-80, int(result2.shape[0]*0.3)], 
            [30, result2.shape[0]-30], [result2.shape[1]-30, result2.shape[0]-30],
            [int(result2.shape[1]/2+80), int(result2.shape[0]*0.3)]]
   p0 = (30, result2.shape[0]-30)    
   p1 = (result2.shape[1]-30, int(result2.shape[0]*0.30))
   #result2 = cv2.rectangle(result2, p0, p1, col, 3)
   isClosed = True
   result2 = cv2.polylines(result2, [np.array(points)], isClosed, col, 3)
   result2 = cv2.putText(result2, msg, (p0[0]+50, p0[1]-40), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)  
   t_text = time_convert(t_load2-t0_load2)
   result2 = cv2.putText(result2, t_text, (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)  
   if not n_frames%10:
       t1 = time.time()
       fps = int(n_frames/(t1-t0))
       t0 = t1
       n_frames = 0
   n_frames+=2
   result1 = cv2.putText(result1, "FPS: {0}".format(fps), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1)  
   result2 = cv2.putText(result2, "FPS: {0}".format(fps), (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 1)  
   cv2.imshow("Cam1", result1)
   cv2.imshow("Cam2", result2)
   if cv2.waitKey(1)==ord('q'):
      break

cap1.release()
cap2.release()
