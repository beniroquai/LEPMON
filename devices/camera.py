import cv2
import os
from vimba import Vimba, PixelFormat

class AlviumCamera:
    def __init__(self, settings_file):
        self.settings_file = settings_file

    def capture_image(self, output_path, blitz_callback=None):
        try:
            with Vimba.get_instance() as vimba:
                cams = vimba.get_all_cameras()
                with cams[0] as cam:
                    cam.set_pixel_format(PixelFormat.Bgr8)
                    cam.load_settings(self.settings_file)
                    
                    # For LED dimming, if needed
                    if blitz_callback:
                        blitz_callback("up")
                    
                    frame = cam.get_frame(timeout_ms=10000).as_opencv_image()
                    
                    if blitz_callback:
                        blitz_callback("down")
                    
                    cv2.imwrite(output_path, frame)
        except Exception as e:
            # log or re-raise
            pass

class ArducamCamera:
    def __init__(self):
        pass

    def capture_image(self, output_path, blitz_callback=None):
        command = f"libcamera-still -t 5000 -n -o {output_path}"
        if blitz_callback:
            blitz_callback("up")
        os.system(command)
        if blitz_callback:
            blitz_callback("down")
