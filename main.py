from PIL import Image
import serial

sample_data = bytes([100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200, 100, 200, 100, 200, 100, 200, 50, 50, 50, 50, 50, 50, 10, 80, 10, 80, 50, 90, 200, 200, 200, 200, 200, 200])

def main():
    image = get_image_from_serial_connection('/dev/ttyUSB0', 115200, 60, 153600, 320)
    #image = create_image_from_binary(sample_data, 12)
    image.show()

def get_image_from_serial_connection(device, baudrate, timeout, data_size, image_width):
    data = get_data_from_serial_connection(device, baudrate, timeout, data_size)
    image = create_image_from_binary(data, image_width)
    return image

def get_data_from_serial_connection(device, baudrate, timeout, size):
    with serial.Serial(device, baudrate, timeout=timeout) as serial_connection:
        data = serial_connection.read(size)

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
            color_r = combined_bytes & 0xF800
            color_g = combined_bytes & 0x07E0
            color_b = combined_bytes & 0x001F
            pixel_color = (color_r, color_g, color_b)
            pixels[x,y] = pixel_color
    return image

if __name__ == '__main__':
    main()

