#!/usr/bin/venv python3
import threading
from CamControl import Camera

#Instantiate Camera object with 4 cameras attached by default. A warning will be printed
#out in the console for each camera device that could not be initialized
#TODO:
# 1. Allow the initialization of Camera with only the devices availabe at /dev/video*
def main():
   cam = Camera(4)

   # Initialize a capturing loop on a separated thread
   capture_thread = threading.Thread(target=cam.capture_loop)
   capture_thread.start()
   while(True):
      print('.')
      str64 = cam.encode64(0)
      if str64:
         break
   print(str64)
   cam.is_capturing = False
   

if __name__=="__main__":
   main()
