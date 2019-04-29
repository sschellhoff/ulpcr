from PIL import Image
import serial
import time

# Only required for easier image handling / updating, e.g. inline images in ipython
import matplotlib.pyplot as plt
import numpy

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
    while True:
        #image = get_image_from_serial_connection('/dev/ttyUSB0', 115200, 60, 153600, 320)
        image = get_image_from_serial_connection('COM44', 115200, 60, 153600, 320)
        #image = create_image_from_binary(sample_data, 12)
        # Use one of the following two options
        # a) Show with matplotlib which can display inline graphics in ipython or has a qt frontend
        plt.imshow(numpy.asarray(image))
        plt.show()
        print()
        # b) Use the default Pillow approach to call an external application
        #image.show()

def get_image_from_serial_connection(device, baudrate, timeout, data_size, image_width):
    data = get_data_from_serial_connection(device, baudrate, timeout, data_size)
    image = create_image_from_binary(data, image_width)
    return image

def get_data_from_serial_connection(device, baudrate, timeout, size):
    # Not very nice, but working: We read the whole image byte by byte and reset
    # the image input whenever we encounter a break of more than .5 seconds
    # between two input bytes. As the uC is making breaks between two images,
    # this synchronizes image reception.
    outbuffer = bytearray(size)
    with serial.Serial(device, baudrate, timeout=timeout) as serial_connection:
        bytecnt = 0
        last_timestamp = 0
        while bytecnt < size: # this could end up in an infinite loop if misconfigured
            current_byte = serial_connection.read(1)
            current_timestamp = time.time()
            if current_timestamp - last_timestamp > .500: # if there was a break, reset image
                bytecnt = 0
            last_timestamp = current_timestamp
            outbuffer[bytecnt] = current_byte[0]
            bytecnt += 1
            if bytecnt % 1000 == 0: # For debugging: Show the current progress
                print('\r            \r', round(bytecnt / size * 100), '%', end='')
        #data = serial_connection.read(size)
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

if __name__ == '__main__':
    main()

