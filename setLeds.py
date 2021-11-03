import re
import os
import board
import neopixel
import adafruit_fancyled.adafruit_fancyled as fancy
import threading
import socket

PORT = 2023

bindsocket = socket.socket()
bindsocket.bind(('', PORT))
bindsocket.listen(5)
print("listening...")

def clientInputLoop(sock, fromaddr):
    NUM_LEDS = int(os.environ['NUMLEDS'])
    BRIGHTNESS = 0.1
    t1 = None
    stopPreset = False
    pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)

    def check_decimal(s) -> bool:
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True
    
    def preset1(stop):
        # Declare a 6-element RGB rainbow palette
        palette = [
            fancy.CRGB(0.66, 0.0, 1.0),  # purple
            fancy.CRGB(0.0, 1.0, 1.0),  # nitro blue
            fancy.CRGB(0.0, 0.75, 0.5),  # mint green
        ]

        offset = 0  # Positional offset into color palette to get it to 'spin'

        while not stop():
            for i in range(NUM_LEDS):
                # Load each pixel's color from the palette using an offset, run it
                # through the gamma function, pack RGB value and assign to pixel.
                color = fancy.palette_lookup(palette, offset + i / NUM_LEDS)
                color = fancy.gamma_adjust(color, brightness=1.0)
                pixels[i] = color.pack()
            pixels.show()

            offset += 0.002  # Bigger number = faster spin
        print('Preset1 Exited')

    def preset2(stop):
        # Declare a 6-element RGB rainbow palette
        palette = [
            fancy.CRGB(1.0, 0.0, 0.0), # red
            fancy.CRGB(1.0, 0.0, 1.0),  # purple
            fancy.CRGB(1.0, 0.0, 0.5), # pink
        ]

        offset = 0  # Positional offset into color palette to get it to 'spin'

        while not stop():
            for i in range(NUM_LEDS):
                # Load each pixel's color from the palette using an offset, run it
                # through the gamma function, pack RGB value and assign to pixel.
                color = fancy.palette_lookup(palette, offset + i / NUM_LEDS)
                color = fancy.gamma_adjust(color, brightness=1.0)
                pixels[i] = color.pack()
            pixels.show()

            offset += 0.002  # Bigger number = faster spin
        print('Preset2 Exited')

    while True:
        try:
            #read led data from the socket
            clientData = sock.recv(24).decode('utf-8').strip() #expected format: 'R,G,B[,Brightness]'
            
            if clientData == '':
                break

            #check if the input is clean
            is_clean = True
            match = re.fullmatch("preset\d", clientData)
            #if the client is setting the preset otherwise check rgb color
            if match and clientData in dir():
                is_clean = True 
            else:
                if clientData.count(',') < 2:
                    is_clean = False
                dataSplit = clientData.split(',')
                if not check_decimal(dataSplit[0]) or not check_decimal(dataSplit[1]) or not check_decimal(dataSplit[2]):
                    is_clean = False
                if len(dataSplit) == 4 and not check_decimal(dataSplit[3]):
                    is_clean = False
            if not is_clean:
                print('ignoring:', clientData)
                continue

            if t1 and t1.is_alive:
                    stopPreset = True
                    t1.join()
            if match:
                stopPreset = False
                if match.string == "preset1":
                    t1 = threading.Thread(target=preset1, args=((lambda: stopPreset),))
                    t1.start()
                elif match.string == "preset2":
                    t1 = threading.Thread(target=preset2, args=((lambda: stopPreset),))
                    t1.start()
            else:
                dataSplit = clientData.split(',')
                #if the brightness was sent, reset the pixel brightness
                if len(dataSplit) == 4:
                    pixels.brightness = float(dataSplit[3])
                    print("Brighness="+str(pixels.brightness))
                #set all led color
                
                pixels.fill((int(dataSplit[0]), int(dataSplit[1]), int(dataSplit[2])))
                #update pixels
                pixels.show()
            print(fromaddr, '->', clientData)
        except Exception as e:
            sock.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both1
            sock.close()
            # connection error event here, maybe reconnect
            print('Error:', e, type(e))
            return
        except ConnectionResetError as eConn:
            print('ConnectionResetError:', eConn)
            return

while True:
    newsocket, fromaddr = bindsocket.accept()
    print('Connection from:', fromaddr)
    t1 = threading.Thread(target=clientInputLoop, args=(newsocket,fromaddr,))
    t1.start()
