from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.views import APIView

import threading
from core.camera.CamControl import Camera

#Instantiate Camera object with 4 cameras attached by default. A warning will be printed
#out in the console for each camera device that could not be initialized
#TODO:
# 1. Allow the initialization of Camera with only the devices availabe at /dev/video*
cam = Camera(4)

# Initialize a capturing loop on a separated thread
capture_thread = threading.Thread(target=cam.capture_loop)
capture_thread.start()

class HomeView(APIView):
   def get(self, request, *args, **kwargs):
      #print("Request data: ", request.data)
      return Response({"status":cam.status, "is_capturing":cam.is_capturing, "is_drawing_bboxes":cam.is_drawing_bboxes, "FPS":cam.fps})

class DeviceView(APIView):
   def get(self, request, *args, **kwargs):
      params = dict(request.query_params)
      _id = 0
      if 'id' in params.keys():
         try:
            _id = int(params['id'][0])
         except ValueError:
            return Response({"error":"id GET param must be an integer within range (0, {0})".format(len(cam.capture_devices)-1)})
         if (_id > len(cam.capture_devices)-1) or (_id < 0):
            _id = 0
      return Response({"cam-id":_id, "status":cam.status[_id], "QRC-data":cam.symbols[_id], "bboxes":cam.bboxes[_id], "img-base64":cam.encode64(_id)})

class StartCapturingView(APIView):
   def get(self, request, *args, **kwargs):
      if not cam.is_capturing:
         cam.is_capturing = True
         # Initialize a new capturing loop on a separated thread
         capture_thread = threading.Thread(target=cam.capture_loop)
         capture_thread.start()
      return Response({"status":cam.status, "is_capturing":cam.is_capturing, "is_drawing_bboxes":cam.is_drawing_bboxes, "FPS":cam.fps})

class StopCapturingView(APIView):
   def get(self, request, *args, **kwargs):
      if cam.is_capturing:
         cam.is_capturing = False
      return Response({"status":cam.status, "is_capturing":cam.is_capturing, "is_drawing_bboxes":cam.is_drawing_bboxes, "FPS":cam.fps})
