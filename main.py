from PIL import Image
import serial
import time

from queue import Queue

# Only required for easier image handling / updating, e.g. inline images in ipython
import matplotlib.pyplot as plt
import numpy

WIDTH = 320
HEIGHT = 240

sample_data = bytes([255, 255, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200,
                     100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200])

def main():
    with serial.Serial('COM44', 115200) as serial_connection:
        receiver = ImageReceiver(serial_connection, WIDTH, HEIGHT)
        transmitter = CommandTransmitter(serial_connection, receiver)
        is_running = True
        while is_running:
            command = input("Command: ")
            if command.lower() == "quit" or command.lower() == "q":
                is_running = False
            else:
                command_words = command.split(" ")
                if command_words[0] == "WRITE":
                    try:
                        address = dec_hex(command_words[1])
                        value = dec_hex(command_words[2])
                        # Currently, the board is only able to receive commands when
                        # it is not transmitting data itself. Therefore, the board
                        # makes a short break after transmitting the image. We have
                        # to wait for this break to send our commands. This happens
                        # asynchronously in the CommandTransmitter module now.
                        #serial_connection.write(bytes(command+"\n", "ascii"))
                        transmitter.append(bytes("WRITE "+str(address)+" "+str(value)+"\n", "ascii"))
                    except ValueError:
                        print("Invalid number given.")
                else:
                    print("please use \"WRITE NUMBER NUMBER\" as command")
        receiver.stop()
        transmitter.stop()
        receiver.join()
        transmitter.join()

def single_command(command):
    with serial.Serial('COM44', 115200) as serial_connection:
        # Wait for the end of a transmission. Currently, the uC can not receive
        # anything while transmitting.
        print('Waiting for an image transmission break ...')
        last_rx = time.time()
        while time.time() - last_rx < 1:
            if serial_connection.inWaiting():
                serial_connection.read(1)
                last_rx = time.time()
        # Then, send command
        print('Sending command and waiting for a response.')
        serial_connection.write(bytes(command+"\n", "ascii"))
        # Finally, wait for response
        last_rx = time.time()
        while time.time()-last_rx < 2:
            if serial_connection.inWaiting():
                b = serial_connection.read(1)
                last_rx = time.time()
                print(b.decode("ascii"), end='') # possible UnicodeDecodeError whenever there is a byte received which is not in 0..127
        print()
    
def single_image():
    with serial.Serial('COM44', 115200) as serial_connection:
        data = get_data_from_serial_connection(serial_connection, WIDTH*HEIGHT*2)
        image = create_image_from_binary(data, WIDTH, HEIGHT, rgb565, 2)
        #image = create_image_from_binary(sample_data, 12)
        # Use one of the following two options
        # a) Show with matplotlib which can display inline graphics in ipython or has a qt frontend
        plt.imshow(numpy.asarray(image))
        plt.show()
        # b) Use the default Pillow approach to call an external application
        #image.show()
        return data, image

# Inspired by (taken from) https://stackoverflow.com/a/325528/805673
import threading
class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class ImageReceiver(StoppableThread):
    def __init__(self, serial_connection, width, height):
        super().__init__()
        self.serial_connection = serial_connection
        self.width = width
        self.height = height
        self.last_rx = 0
        self.start() # Thread.start()

    def run(self):
        while not self.stopped():
            data = get_data_from_serial_connection(self.serial_connection, self.width*self.height*2, self)
            image = create_image_from_binary(data, self.width, self.height, rgb565, 2)
            #image = create_image_from_binary(sample_data, 12)
            # Use one of the following two options
            # a) Show with matplotlib which can display inline graphics in ipython or has a qt frontend
            plt.imshow(numpy.asarray(image))
            plt.show()
            print()
            # b) Use the default Pillow approach to call an external application
            #image.show()

class CommandTransmitter(StoppableThread):
    def __init__(self, serial_connection, image_receiver):
        super().__init__()
        self.serial_connection = serial_connection
        self.image_receiver = image_receiver
        self.commands = Queue()
        self.start()
    
    def append(self, command):
        self.commands.put(command)
    
    def run(self):
        while not self.stopped():
            # Wait until there is a 2 seconds break after receiving
            if time.time() - self.image_receiver.last_rx < 2:
                time.sleep(.1) # Limit CPU load
                continue
            # Then, until the queue is empty, pop commands and transmit them
            while not self.commands.empty():
                command = self.commands.get()
                self.serial_connection.write(command)

def get_data_from_serial_connection(serial_connection, size, image_receiver=None):
    # Not very nice, but working: We read the whole image byte by byte and reset
    # the image input whenever we encounter a break of more than .5 seconds
    # between two input bytes. As the uC is making breaks between two images,
    # this synchronizes image reception.
    outbuffer = bytearray(size)
    bytecnt = 0
    last_timestamp = 0
    while bytecnt < size and (image_receiver == None or not image_receiver.stopped()): # this could end up in an infinite loop if misconfigured
        current_byte = serial_connection.read(1)
        image_receiver.last_rx = time.time()
        current_timestamp = time.time()
        if current_timestamp - last_timestamp > .500: # if there was a break, reset image
            if bytecnt:
                print(outbuffer[0:min(bytecnt, 100)])
            bytecnt = 0
        last_timestamp = current_timestamp
        outbuffer[bytecnt] = current_byte[0]
        bytecnt += 1
        if bytecnt % 1000 == 0: # For debugging: Show the current progress
            print('\r            \r', round(bytecnt / size * 100), '%', end='')
    data = bytes(outbuffer)
    return data

def create_image_from_binary(data, width, height, bytes_to_pixel_func, bytes_per_pixel):
    image = Image.new("RGB", (width, height), color='white')
    pixels = image.load()
    for col in range(image.size[0]):
        for row in range(image.size[1]):
            # Calculate the first index where data/bytes for the current pixel
            # can be found:
            # The uC has a data buffer of width*height*2 to be able to store
            # YUB or RGB which needs 2 bytes per pixel and always sends the
            # whole buffer to us.
            # The beginning of a line is therefore: line-index * 2 * width
            # Depending on the data format, the uC receives one or two pclk
            # interrupts per pixel. On each interrupt, the data pointer is
            # incremented.
            # Therefore, we have to add column-index * bytes-per-pixel to the
            # beginning of a line.
            first_index = row * 2 * width + col * bytes_per_pixel
            pixels[col,row] = bytes_to_pixel_func(data[first_index:first_index+bytes_per_pixel])
    return image

def rgb565(two_bytes):
    combined_bytes = (two_bytes[0] << 8) + two_bytes[1]
    # The shift compensates the position, the scaling factor compensates the value range
    color_r = ((combined_bytes & 0xF800) >> 11) * 8
    color_g = ((combined_bytes & 0x07E0) >> 5) * 4
    color_b = ((combined_bytes & 0x001F) >> 0) * 8
    pixel_color = (color_r, color_g, color_b)
    return pixel_color
def raw_bw(byte):
    val = byte[0]
    pixel_color = (val, val, val)
    print('raw conversion does not seem to work!')
    return pixel_color
def yuv(two_bytes):
    value = two_bytes[1]
    return (value, value, value)

def dec_hex(string):
    try:
        value = int(string)
        return value
    except ValueError:
        pass
    return int(string, 16)

if __name__ == '__main__':
    #data, image = single_image()
    main()
    pass
