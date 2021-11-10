import json
# import board
# import neopixel
# import adafruit_fancyled.adafruit_fancyled as fancy
import threading
import socket

PORT = 2023

bindsocket = socket.socket()
bindsocket.bind(('', PORT))
bindsocket.listen(5)
print("listening...")

def clientInputLoop(sock, fromaddr):
    def is_clean(input_data_split):
        if len(input_data_split) != 5:
            return False
        for data in input_data_split[1:]:
            if not check_decimal(data):
                return False
        return True

    def check_decimal(s) -> bool:
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True

    def preset(preset, stop_check):
        import colorsys
        # Declare a 6-element RGB rainbow palette
        rgb1 = colorsys.hsv_to_rgb(int(preset[0])/360, 1.0, 1.0)
        rgb2 = colorsys.hsv_to_rgb(int(preset[1])/360, 1.0, 1.0)
        rgb3 = colorsys.hsv_to_rgb(int(preset[2])/360, 1.0, 1.0)
        palette = [
            fancy.CRGB(rgb1[0], rgb1[1], rgb1[2]),
            fancy.CRGB(rgb2[0], rgb2[1], rgb2[2]),
            fancy.CRGB(rgb3[0], rgb3[1], rgb3[2]),
        ]

        offset = 0  # Positional offset into color palette to get it to 'spin'

        while not stop_check():
            for i in range(NUM_LEDS):
                # Load each pixel's color from the palette using an offset, run it
                # through the gamma function, pack RGB value and assign to pixel.
                color = fancy.palette_lookup(palette, offset + i / NUM_LEDS)
                color = fancy.gamma_adjust(color, brightness=1.0)
                pixels[i] = color.pack()
            pixels.show()

            offset += 0.002  # Bigger number = faster spin
    
    ledconffile = open("/home/pi/.LedConsts.conf", "r")
    ledconfjson = json.loads(ledconffile.read())
    NUMLEDS = int(ledconfjson['NUMLEDS'])
    HOSTNAME = str(ledconfjson['HOSTNAME'])
    ledconffile.close()
    BRIGHTNESS = 0.1
    pixels = neopixel.NeoPixel(board.D18, NUMLEDS, brightness=BRIGHTNESS, auto_write=False)
    stopPreset = False
    t1 = threading.Thread(target=preset, args=([280, 180, 165], (lambda: stopPreset),))
    t1.start()

    while True:
        try:
            #read led data from the socket
            clientData = sock.recv(24).decode('utf-8').strip() #expected format: 'type,R,G,B,Brightness[,names]'
            if clientData == '':
                break
            dataSplit = clientData.split(',')
            #check if data is clean with no attempt to sanitize
            if HOSTNAME not in dataSplit or not is_clean(dataSplit):
                print('ignoring:', clientData)
                continue

            #set brightness
            if pixels.brightness != float(dataSplit[4])/(max(100, NUMLEDS)*1.33):
                pixels.brightness = float(dataSplit[4])/(max(100, NUMLEDS)*1.33)
                print("Brighness="+str(pixels.brightness))
            #if the preset is running then stop it
            if t1 and t1.is_alive:
                stopPreset = True
                t1.join()
            if dataSplit[0] == 'preset':
                stopPreset = False
                t1 = threading.Thread(target=preset, args=(dataSplit[1:4], (lambda: stopPreset),))
                t1.start()
            elif dataSplit[0] == 'static':
                pixels.fill((int(dataSplit[1]), int(dataSplit[2]), int(dataSplit[3])))
                pixels.show()
            print(fromaddr,'->',clientData)
            logfile = open("setLeds.log", "a")
            logfile.write(str(fromaddr)+' -> '+str(clientData)+'\n')
            logfile.close()

        except Exception as e:
            if t1 and t1.is_alive:
                stopPreset = True
                t1.join()
            # connection error event here, maybe reconnect
            print('Error:', e, type(e))
            return
        except ConnectionResetError as eConn:
            sock.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both
            sock.close()
            print('ConnectionResetError:', eConn)
            return
    if t1 and t1.is_alive:
        stopPreset = True
        t1.join()
    sock.shutdown(2)
    sock.close()
    
from datetime import datetime
logfile = open("setLeds.log", "a")
logfile.write(str(datetime.now()))
logfile.close()

while True:
    newsocket, fromaddr = bindsocket.accept()
    print('Connection from:', fromaddr)
    t1 = threading.Thread(target=clientInputLoop, args=(newsocket,fromaddr,))
    t1.start()
