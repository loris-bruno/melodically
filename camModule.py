
from picamera import PiCamera
import time

frameWidth = 2592
frameHeight = 1936

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (frameWidth, frameHeight)
# let the camera start
time.sleep(2)
    
def capture_camera(imageName):
    camera.capture(imageName)
