import pyautogui as pg
import os
from PIL import Image, ImageOps
import pytesseract
import time

import platform
if platform.system() == "Darwin":
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
elif platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

fps = 15

xywhs = {
    "Darwin": {
        "prompts": (900, 50, 1050, 110),
        "signal": (600, 950, 680, 1035),
        "speed": (720, 1033, 763, 1053),
        "speedLimit": (720, 1050, 765, 1072),
        "distanceToStation": (860, 1050, 1000, 1072)
    },
    "Windows": {
        "prompts": (900, 50, 1050, 110),
        "signal": (510, 923, 602, 1016),
        "speed": (762, 1018, 814, 1046),
        "speedLimit": (762, 1043, 823, 1064),
        "distanceToStation": (873, 1045, 991, 1063)
    }
}

RED = 1
YELLOW = 2
GREEN = 3

def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)

def tesseract_image_fix(img, basewidth=100):
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.LANCZOS)
    return change_contrast(img, 100)

def accelerate():
    pg.keyDown('w')
    time.sleep(0.1)
    pg.keyUp('w')
    time.sleep(0.2)
    
def brake():
    pg.keyDown('s')
    time.sleep(0.1)
    pg.keyUp('s')
    time.sleep(0.2)

def main():
    driving = True
    slowing_for_station = False
    
    last_speed = -1
    
    throttle_notch = -4
    
    dt = 1/fps
    while True:
        startT = time.time()
        
        # Get screenshot
        orig_img = pg.screenshot(region=(0, 0, 1920, 1080))
        orig_img.convert('RGB')
        
        # Prompts
        xywh = xywhs[platform.system()]["prompts"]
        img = tesseract_image_fix(orig_img.crop(xywh), basewidth=500)
        img.save("prompts.png")
        prompts_text = pytesseract.image_to_string(img).lower()
        
        if "aws" in prompts_text:
            pg.press('q')
            time.sleep(0.5)
            continue
        
        if "open" in prompts_text and "doors" in prompts_text:
            pg.press('t')
            time.sleep(0.5)
            continue
        
        if "close" in prompts_text and "doors" in prompts_text and "closed" not in prompts_text:
            for i in range(4):
                pg.press('t')
                time.sleep(0.5)
            throttle_notch = -4
            
        if "buzz" in prompts_text and "guard" in prompts_text:
            pg.press('t')
            time.sleep(0.5)
            throttle_notch = -4
            
        os.remove("prompts.png")
        
        driving = True
        
        # Signal
        xywh = xywhs[platform.system()]["signal"]
        img = orig_img.crop(xywh)
        img.save("signal.png")
        current_signal = GREEN
        # Check colour of signal
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                pixel = img.getpixel((x, y))
                r, g, b = pixel[:3]
                if r > 200 and g < 100 and b < 100:
                    current_signal = RED
                elif r > 150 and g > 150 and b < 150:
                    current_signal = YELLOW
            if current_signal != GREEN:
                break
        os.remove("signal.png")
        
        # Increase contrast for better OCR
        orig_img = orig_img.convert('L')
        
        # Current Speed
        xywh = xywhs[platform.system()]["speed"]
        img = tesseract_image_fix(orig_img.crop(xywh))
        img.save("speed.png")
        speed_text = pytesseract.image_to_string(img)
        try:
            current_speed = int(speed_text)
        except:
            current_speed = 0
        os.remove("speed.png")
        
        # Speed Limit
        xywh = xywhs[platform.system()]["speedLimit"]
        img = ImageOps.colorize(tesseract_image_fix(orig_img.crop(xywh)), black="black", white="white", mid="white")
        img.save("speedLimit.png")
        # has_yellow = False
        # for x in range(img.size[0]):
        #     for y in range(img.size[1]):
        #         r, g, b = img.getpixel((x, y))
        #         if r > 200 and g > 200 and b < 100:
        #             has_yellow = True
        #             break
        #     if has_yellow:
        #         break
        speed_limit_text = pytesseract.image_to_string(img)
        try:
            speed_limit = int(speed_limit_text)
            if speed_limit == 7:
                speed_limit = 70
        except:
            speed_limit = 30
            
        if current_signal == YELLOW and speed_limit > 45:
            speed_limit = 45
        elif current_signal == RED:
            speed_limit = 0
            
        os.remove("speedLimit.png")
            
        # Distance to station
        xywh = xywhs[platform.system()]["distanceToStation"]
        img = tesseract_image_fix(orig_img.crop(xywh), basewidth=500)
        img.save("distanceToStation.png")
        distance_to_station_text = pytesseract.image_to_string(img)
        if "a" in distance_to_station_text:
            if slowing_for_station:
                pg.press('b')
            driving = False
            slowing_for_station = False
            last_speed = -1
            continue
        distance_digits = ""
        for c in distance_to_station_text:
            if c.isdigit() or c == ".":
                distance_digits += c
        try:
            distance_to_station = float(distance_digits)
        except:
            distance_to_station = 0
        os.remove("distanceToStation.png")
            
        # Close to station
        if distance_to_station*100 < current_speed*0.8 or slowing_for_station:
            speed_limit = 25
            slowing_for_station = True
        
        # print(current_speed, speed_limit, throttle_notch, distance_to_station, driving, slowing_for_station, current_signal)
        
        if last_speed - current_speed < 15:
            
            # Drive
            if driving:
                if current_speed < speed_limit - 5:
                    while throttle_notch != 4:
                        accelerate()
                        throttle_notch += 1
                elif speed_limit == 0:
                    while throttle_notch != -4:
                        brake()
                        throttle_notch -= 1
                elif current_speed > speed_limit + 5:
                    max_brake_notch = -4
                    if slowing_for_station:
                        max_brake_notch = -3
                    while throttle_notch != max_brake_notch:
                        if throttle_notch < max_brake_notch:
                            accelerate()
                            throttle_notch += 1
                        else:
                            brake()
                            throttle_notch -= 1
                else:
                    while throttle_notch != 0:
                        if throttle_notch < 0:
                            accelerate()
                            throttle_notch += 1
                        else:
                            brake()
                            throttle_notch -= 1
                
            last_speed = current_speed
        
        # Stick to fps
        endT = time.time()
        time.sleep(max(0, dt - (endT - startT)))
        
    
if __name__ == "__main__":
    main()