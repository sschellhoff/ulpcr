from PIL import Image
import serial
import time

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
        is_running = True
        while is_running:
            command = input("Type any key to stop the program")
            if command == "quit" or command == "QUIT" or command == "Quit" or command == "q" or command == "Q":
                is_running = False
            else:
                command_words = command.split(" ")
                if command_words[0] == "WRITE" and is_integer(command_words[1]) and is_integer(command_words[2]):
                    serial.send(command + "\n")
                else:
                    print("please use \"WRITE NUMBER NUMBER\" as command")
        receiver.stop()
        receiver.join()
"""
    while True:
        with serial.Serial('COM44', 115200) as serial_connection:
            data = get_data_from_serial_connection(serial_connection, WIDTH*HEIGHT*2)
            image = create_image_from_binary(data, WIDTH)
            #image = create_image_from_binary(sample_data, 12)
            # Use one of the following two options
            # a) Show with matplotlib which can display inline graphics in ipython or has a qt frontend
            plt.imshow(numpy.asarray(image))
            plt.show()
            print()
            # b) Use the default Pillow approach to call an external application
            #image.show()
            """

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
        self.start() # Thread.start()

    def run(self):
        while not self.stopped():
            data = get_data_from_serial_connection(self.serial_connection, self.width*self.height*2, self)
            image = create_image_from_binary(data, self.width)
            #image = create_image_from_binary(sample_data, 12)
            # Use one of the following two options
            # a) Show with matplotlib which can display inline graphics in ipython or has a qt frontend
            plt.imshow(numpy.asarray(image))
            plt.show()
            print()
            # b) Use the default Pillow approach to call an external application
            #image.show()

def get_data_from_serial_connection(serial_connection, size, stoppable_thread=None):
    # Not very nice, but working: We read the whole image byte by byte and reset
    # the image input whenever we encounter a break of more than .5 seconds
    # between two input bytes. As the uC is making breaks between two images,
    # this synchronizes image reception.
    outbuffer = bytearray(size)
    bytecnt = 0
    last_timestamp = 0
    while bytecnt < size and (stoppable_thread == None or not stoppable_thread.stopped()): # this could end up in an infinite loop if misconfigured
        current_byte = serial_connection.read(1)
        current_timestamp = time.time()
        if current_timestamp - last_timestamp > .500: # if there was a break, reset image
            bytecnt = 0
        last_timestamp = current_timestamp
        outbuffer[bytecnt] = current_byte[0]
        bytecnt += 1
        if bytecnt % 1000 == 0: # For debugging: Show the current progress
            print('\r            \r', round(bytecnt / size * 100), '%', end='')
    data = bytes(outbuffer)
    return data

def create_image_from_binary(data, width):
    height = (len(data) // width) // 2
    image = Image.new("RGB", (width, height), color='white')
    pixels = image.load()
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            color_index_1_in_data = y * 2 * width + x * 2 # two bytes per color
            color_index_2_in_data = color_index_1_in_data + 1
            if color_index_2_in_data > len(data):
                print("there was some missing data!")
                return image
            byte_1 = data[color_index_1_in_data]
            byte_2 = data[color_index_2_in_data]
            combined_bytes = (byte_1 << 8) | byte_2
            # The shift compensates the position, the scaling factor compensates the value range
            color_r = ((combined_bytes & 0xF800) >> 11) * 8
            color_g = ((combined_bytes & 0x07E0) >> 5) * 4
            color_b = ((combined_bytes & 0x001F) >> 0) * 8
            pixel_color = (color_r, color_g, color_b)
            pixels[x,y] = pixel_color
    return image

def is_integer(string):
    try:
        int(string)
        return True
    except ValueError
        return False

if __name__ == '__main__':
    main()

