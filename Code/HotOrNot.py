import os
import argparse
from time import sleep
from colour import Color
from gpiozero import LED, Button
from signal import pause
import datetime
import storeFileFB
import emailServer

from Adafruit_AMG88xx import Adafruit_AMG88xx
from PIL import Image, ImageDraw, ImageFont
button = Button(17)



while True:
    # parse command line arguments
    parser = argparse.ArgumentParser(description='Take a still image.')
    parser.add_argument('-o','--output', metavar='frame', default='amg88xx_still.jpg', help='specify output filename')
    parser.add_argument('-s','--scale', type=int, default=50, help='specify image scale')
    parser.add_argument('--min', type=float, help='specify minimum temperature')
    parser.add_argument('--max', type=float, help='specify maximum temperature')
    parser.add_argument('--report', action='store_true', default=False, help='show sensor information without saving image')
        
    args = parser.parse_args()
    
    # sensor setup
    NX = 8
    NY = 8
    sensor = Adafruit_AMG88xx()

    # wait for it to boot
    sleep(.1)

    # get sensor readings  
    pixels = sensor.readPixels()
    hot = (max(pixels) + 3)
    print(max(pixels) + 3)
    button.wait_for_press()
    if args.report:
        print ("Min Pixel = {0} C".format(min(pixels)))
        print ("Max Pixel = {0} C".format(max(pixels)))
        print ("Thermistor = {0} C".format(sensor.readThermistor()))
        exit()

    # output image buffer
    image = Image.new("RGB", (NX, NY), "white")
    draw = ImageDraw.Draw(image)
    fnt = ImageFont.truetype("/home/pi/.fonts/ARIAL.TTF", 16)
    # color map
    COLORDEPTH = 256
    colors = list(Color("indigo").range_to(Color("red"), COLORDEPTH))
    colors = [(int(c.red * 255), int(c.green * 255), int(c.blue * 255)) for c in colors]

    #some utility functions
    def constrain(val, min_val, max_val):
        return min(max_val, max(min_val, val))

    def map(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    # map sensor readings to color map
    MINTEMP = min(pixels) if args.min == None else args.min
    MAXTEMP = max(pixels) if args.max == None else args.max
    pixels = [map(p, MINTEMP , MAXTEMP, 0, COLORDEPTH - 1) for p in pixels]

    # create the image
    for ix in range(NX):
        for iy in range(NY):
            draw.point([(ix,iy%NX)], fill=colors[constrain(int(pixels[ix+NX*iy]), 0, COLORDEPTH- 1)])
            
            
    
    # scale and save
    image.resize((NX*args.scale, NY*args.scale), Image.BICUBIC,).save(args.output)
    # This reopens image adds highest temp text and saves the new file
    img = Image.open('/home/pi/Assignment2/amg88xx_still.jpg')
    draw = ImageDraw.Draw(img)
    draw.text((10,10), 'Highest Temp = {0:0.2f} *C'.format(hot), font=fnt, fill=(0, 0, 0))
    currentTime = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    # changes the filename after text is added and increments the file name by 1
    filename = "images/frame{}.jpg"
    counter = 0
    while os.path.isfile(filename.format(counter)):
        counter += 1
    filename = filename.format(counter)
    img.save(filename, quality=100, subsampling=0)
    # Cretes and sends email
    emailServer.text= f'Hi,\n the attached image was taken today at {currentTime} \n Remember In these Uncertain times please proceed with cation. \n Your Visitors temperature is = {hot} *C. \n Our View the image Click https://near-candied-munchkin.glitch.me'
    emailServer.send_mail('lorcancrean12@gmail.com', 'lorcancrean12@gmail.com', 'Door Event',emailServer.text, filename)
    print(f'frame {counter} taken at {currentTime}')
    # Pushes file to firebase
    storeFileFB.store_file(filename)
    storeFileFB.push_db(filename, currentTime)

