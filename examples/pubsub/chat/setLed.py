import board
import neopixel
import threading
import socket

PORT = 2023

bindsocket = socket.socket()
bindsocket.bind(('', PORT))
bindsocket.listen(5)
print("listening...")

def clientInputLoop(sock, fromaddr):
    NUM_LEDS = 512
    BRIGHTNESS = 0.1
    pixels = neopixel.NeoPixel(board.D18, NUM_LEDS, brightness=BRIGHTNESS, auto_write=False)
    def check_decimal(s) -> bool:
        try:
            float(s)
        except ValueError:
            return False
        else:
            return True
    
    def is_clean(clientData) -> bool:
        if clientData == '':
            return False
        if clientData.count(',') < 2:
            return False
        dataSplit = clientData.split(',')
        if not check_decimal(dataSplit[0]) or not check_decimal(dataSplit[1]) or not check_decimal(dataSplit[2]):
            return False
        if len(dataSplit) == 4 and not check_decimal(dataSplit[3]):
            return False
        return True

    while True:
        try:
            #read led data from the socket
            clientData = sock.recv(24).decode('utf-8').strip() #expected format: 'R,G,B[,Brightness]'
            if not is_clean(clientData):
                print('ignoring:', clientData)
                continue
            dataSplit = clientData.split(',')
            #if the brightness was sent, reset the pixel brightness
            if len(dataSplit) == 4:
                print(pixels.brightness)
                pixels.brightness = float(dataSplit[3])
            #set all led color
            print(fromaddr, '->',(int(dataSplit[0]), int(dataSplit[1]), int(dataSplit[2])))
            pixels.fill((int(dataSplit[0]), int(dataSplit[1]), int(dataSplit[2])))
            # #update pixels
            pixels.show()
        except:
            sock.shutdown(2)    # 0 = done receiving, 1 = done sending, 2 = both1
            sock.close()
            # connection error event here, maybe reconnect
            print('connection error')
            return

while True:
    newsocket, fromaddr = bindsocket.accept()
    print('Connection from:', fromaddr)
    t1 = threading.Thread(target=clientInputLoop, args=(newsocket,fromaddr,))
    t1.start()
