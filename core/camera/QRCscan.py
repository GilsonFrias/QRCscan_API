#!/usr/bin/env python3

#QRCscanner by Gilson Frías @ Nodrix, Sept. 9 2021

#This QR code scanner class is based on the Java library boofCV and its Python binding Pyboof. A comparison between boofCV and others libraries for QR code detection and decoding 
#(such as zbar) can be found at: http://boofcv.org/index.php?title=Performance:QrCode

#Frame preprocessing pipeline implemented following this discussion: https://stackoverflow.com/questions/63195577/how-to-locate-qr-code-in-large-image-to-improve-decoding-performance
import cv2
import numpy as np
import pyboof as pb
import json

class QRCscanner(object):

   def __init__(self):
      self.frame = None
      self._bboxes = None
      self._data = None
      self.params = self.load_json("./core/camera/params.json")
      pb.init_memmap()
      self.detector = pb.FactoryFiducial(np.uint8).qrcode()
      self.draw_bboxes = True

   def process_frame(self, img, preprocess=False):
      '''
      Process an input frame and returns the decoded QR codes within the escene alongside      their bboxes.
      '''
      data = []
      bboxes = []
      points = []
      status = ""
      status_msg = ""
      #if not img:
         #return data, bboxes, img, status, status_msg
      if type(img) != type(np.array('')):
         status = "error"
         status_msg = "[ERROR:QRCscanner.process_frame] img expected to be np.array"
         return data, bboxes, img, status, status_msg
      #else: 
      try:
         img_shape = img.shape
         if len(img_shape) <2:
            status = "error"
            status_msg = "[ERROR:QRCscanner.process_frame] img expected to be at least 2 dimmentional"
            return data, bboxes, img, status, status_msg
      except AttributeError:
            status = "error"
            status_msg = "[ERROR:QRCscanner.process_frame] could not extract shape from img"
            return data, bboxes, img, status, status_msg
      
      #1. Convert to gray scale
      resized = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

      #2. Resize frame if necesary
         # *IMPORTANT*: The detector the detector strugles with images with resolutions above (1248, 1664). 
         # It throws a ValueError on the mmap_numpy_to_boof_U8 method. Resizing the image fixes the issue.
      if resized.shape[0]>1200 or resized.shape[1]>1600:
         resized = self.resize_img(resized, self.params["img-zoom"])
         img = self.resize_img(img, self.params["img-zoom"])
      
      if preprocess:
         roi_bboxes = self.find_roi(resized)
         for xmin, ymin, xmax, ymax in roi_bboxes:
            roi = gray[ymin:ymax, xmin:xmax]
            roi = self.resize_img(roi, self.params["roi-zoom"])
            try:
               boof_img = pb.ndarray_to_boof(roi)
               self.detector.detect(boof_img)
            except ValueError:
               status = "error"
               status_msg = "input img dimmensions are too big"
               print(''.join(["[ERROR:QRCscan.process_frame]: ", status_msg]))
               continue
            for barcode in self.detector.detections:
               detected_data = barcode.message
               if detected_data not in data:
                  data.append(detected_data)
                  p = [[int(pair[0]), int(pair[1])] for pair in barcode.bounds.convert_tuple()]
                  p = np.array(p).reshape((-1,1,2))
                  cv2.polylines(resized, [p], True, (255, 200, 200), 10)
                  points.append(p)
      else:
         try:
            boof_img = pb.ndarray_to_boof(resized)
            self.detector.detect(boof_img)
         except ValueError:
            status = "error"
            status_msg = "input img dimmensions are too big"
            print(''.join(["[ERROR:QRCscan.process_frame]: ", status_msg]))
            return (data, points, [], status, status_msg)
         for barcode in self.detector.detections:
            detected_data = barcode.message
            #print("Decoded data:", detected_data)
            if detected_data not in data:
               data.append(detected_data)
               p = [[int(pair[0]), int(pair[1])] for pair in barcode.bounds.convert_tuple()]
               p_array = np.array(p).reshape((-1,1,2))
               if self.draw_bboxes:
                  cv2.polylines(resized, [p_array], True, (255, 200, 200), 10)
                  cv2.polylines(img, [p_array], True, (55, 200, 200), 10)
               img = cv2.putText(img, detected_data, p_array[0][0], cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 200, 200), 3)
               points.append(p)
      status = "ok"
      #return data, [p.tolist() for p in points], img, status, status_msg
      return data, points, img, status, status_msg



   def find_roi(self, img):
      '''
      Find the Regions of Interest that most likely contain QR codes withing a gray scale       image (img). The image is converted in black-and-white and then bounding regions that contain squared geometries are identified and returned
      input:
         img: gray scale image of shape (H, W)
      returns:
         bboxes: a list of tuples where each tuples contains the coordinates of of two oposed vertices of a rectangle (x0, y0, x1, y1).  
      '''
      #1. Convert to black-and-white with thresholding
      _, binary = cv2.threshold(img, self.params["threshold-th"], self.params["threshold-max"], cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

      #2. Dilate image to remove fine elements within the QR code contour
      kernel = np.ones((self.params["dilat-knl-shape"], self.params["dilat-knl-shape"]), np.uint8)
      thresh = cv2.dilate(binary, kernel, iterations=1)

      #3. Find contours on thresh and choose those that more likely correspond to QR codes
      contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
      
         #3.1 Filter contours
      #filt_contours = []
      bboxes = []
      for i in range(len(contours)):
         area = cv2.contourArea(contours[i])
         xmin, ymin, width, height = cv2.boundingRect(contours[i])
         extent = area/(width+height)
         if (extent>self.params["roi-extent"]) and (area>self.params["roi-area"]):
            bboxes.append((xmin, ymin, xmin+width, ymin+height))
            #filt_contours.append(contours[i])
      return bboxes


   
   def resize_img(self, img, scale_percent):
      width = int(img.shape[1] * scale_percent / 100)
      height = int(img.shape[0] * scale_percent / 100)
      dim = (width, height)

      # resize image
      resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA) 
      return resized


   def load_json(self, filename):
      '''
		Reads a JSON file from the filename path. 
		'''
      try:
         with open(filename, 'r') as json_file:
            data = json.load(json_file)
            return data
      except FileNotFoundError:
            print("[Exception]::utils.load_json JSON file not found")

def main():
   scanner = QRCscanner()
   img_files = ['test0.jpg', 'test1.jpg', 'test2.jpg', 'test3.png', 'test4.jpg', 'test5.jpg']
   img = cv2.imread("./test_data/test1.jpg", cv2.IMREAD_COLOR)
   data, points, frame = scanner.process_frame(img)
   print("{} QR codes detected: ".format(len(data)), data)
   print("Located at: ", points) 

if __name__ == "__main__":
   main()
