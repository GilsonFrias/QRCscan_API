#!/usr/bin/env python3

# Sep. 15, 2021. QR Code decoding and Camera handling/cheduling script by Gilson Frías for Nodrix.

import cv2
import numpy as np
import base64
import pyboof as pb
from core.camera.QRCscan import QRCscanner
#from QRCscan import QRCscanner
import subprocess
import time

#TODO:
# 1. Implement reconfigure() method to reconnect to capture device that was not 
#    available at the initial setup_device call or that was disconnected after
# 2. Implement get_avail_res to get a list of all possible resolutions supported

class Camera(object):

   def __init__(self, N_DEVICES=1):
      caps = list(map(self.setup_device, [dev for dev in range(0, N_DEVICES*2, 2)]))
      self.capture_devices = [cap[0] for cap in caps]
      self.frames = [None for n in range(len(self.capture_devices))]
      self.symbols = [None for n in range(len(self.capture_devices))]
      self.bboxes = [None for n in range(len(self.capture_devices))]
      self.status = [cap[1] for cap in caps]
      self.specs = [cap[2] for cap in caps]
      self.time_stamps = [0]*len(self.capture_devices)
      self.is_capturing = False
      self.detector = QRCscanner()
      self.is_drawing_bboxes = self.detector.draw_bboxes
      self.fps = 0
      self.frames_count = 0

   def encode64(self, frame_indx):
      '''
      '''
      frame = self.frames[frame_indx]
      if frame is not None:
         _, frame = cv2.imencode('.jpg', frame)
         frame = base64.b64encode(frame)
      return frame

   def get_device_description(self, source):
      '''
      Retrieve the camera description of a /dev/video{source} camera device by calling
      on the v4l2-ctl --list-devices command
      '''
      #Confirm that v4l2-ctl is available
      out, err = subprocess.Popen(["which", "v4l2-ctl"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      if len(out.decode())==0:
         err = "v4l2-ctl not found"
         return "", err
      #cmd = ["/usr/bin/v4l2-ctl", "--list-devices"]
      cmd = ["/usr/bin/v4l2-ctl", "-d{}".format(source), "-D"]
      out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
      desc = out.decode()
      err = err.decode()
      return desc, err

   def test_device(self, source):
      '''
      Test the state of a recording device /dev/video[source]
      As suggested in the Stack Overflow thread: https://stackoverflow.com/questions/48049886/how-to-correctly-check-if-a-camera-is-available
      '''
      status = "ok"
      status_msg = ""
      cap = cv2.VideoCapture(source)
      if cap is None or not cap.isOpened():
         status=None
         status_msg = "[Warning::QRCcam.test_device] unable to open video device: /dev/video{0}".format(source)
         return (None, status, status_msg)
      status_msg, _ = self.get_device_description(source) 
      return cap, status, status_msg

   def set_resolution(self, cap, w, h):
      '''
      Set the Width and Height resolution of a VideoCapture device
      '''
      ret_w = cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
      ret_h = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
      return ret_w and ret_h  
   
   def setup_device(self, source):
      '''
      ''' 
      #Make sure that an int or str representation of an int was passed as sources
      if isinstance(source, str):
         try:
            source = int(source)
         except ValueError:
            status = "error"
            status_msg = "[ERROR::QRCcam.setup_device] sources must be an int or str representation of int"
            return None, status, status_msg
      elif not isinstance(source, int):
         status = "error"
         status_msg = "[ERROR::QRCcam.setup_device] sources must be an int or str representation of int"
         return None, status, status_msg
      #Instantiate and test capture device
      cap, status, status_msg = self.test_device(source)
      #Adjust camera resolution
      if cap:
         _ = self.set_resolution(cap, 800, 600)
      return cap, status, status_msg

   def capture_loop(self):
      '''
      '''
      n_frames = 0
      t0 = 0
      t1 = 0
      if any(self.capture_devices):
         self.is_capturing = True
      while(self.is_capturing):
         for i in range(len(self.capture_devices)):
            if self.capture_devices[i]:
               #Capture frame
               ret, frame = self.capture_devices[i].read()
               #Process frame in QRC detector/decoder
               try:
                  _data, _bboxes, result_frame, _status, _status_msg = self.detector.process_frame(frame)
               #If the QRC detector cannot process frame, try to catch the error
               #TODO:
               # 1. Look for ways of catching errors related to the JVM process invoked 
               #    from Pyboof
               except ValueError:
                  _status = "error"
                  _status_msg = "Could not unpack return values form QRCscan.process_frames"
                  self.status[i] = {"status":_status, "status_info":_status_msg}
                  continue
               #Store new values on the class variables
               self.frames[i] = result_frame
               self.bboxes[i] = _bboxes
                  #If a change of symbol occurs (i.e. a new id is found in frame or an old id is not longer in frame), mark the moment of change with a unix timestamp
               if self.symbols[i]!=_data:
                  self.time_stamps[i] = int(time.time())
                  self.symbols[i] = _data
               self.status[i] = {"status":_status, "status_info":_status_msg, "last_detection_change":self.time_stamps[i]}
               #Calculate FPS
               n_frames+=1
               if not n_frames%10:
                  t1 = time.time()
                  self.fps = int(n_frames/(t1-t0))
                  t0 = t1
                  n_frames = 0

      

