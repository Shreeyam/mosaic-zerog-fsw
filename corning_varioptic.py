import serial

class corning_usb:
    # Register maps 
    REG_FOC_LSB =   0x00
    REG_FOC_MSB =   0x01
    REG_EEPROM =    0x02
    REG_MODE =      0x03
    REG_VERSION =   0x05
    REG_FAULT =     0x0A

    # Fixed settings for liquid lens
    BAUDRATE =      57600

    # Write frames
    FRAME_STX =     0x02
    FRAME_WRITE =   0x37
    FRAME_READ =    0x38
    FRAME_ACK =     0x06
    FRAME_NACK =    0x15

    def __init__(self, port):
        # 57600 baud, 1 stop bit, no parity
        self.device = serial.Serial(port=port, baudrate=self.BAUDRATE, stopbits=1)


    def __del__(self):
        # close serial port before garbage collection
        self.device.close()

    def calc_crc(self, frame):
        # 1-byte sum
        return sum(frame) % 256 

    # Write a frame and check acknowledgement
    # Format is [FRAME_STX, FRAME_WRITE, ADDRESS, NB_DATA, [DATA], CRC]
    # CRC format is 1 byte sum of all bytes
    # reg is first register
    # data is scalar, or list
    # returns True for successful transmission, false otherwise
    def write_frame_ack(self, reg, data):
        nb_data = len(data) if isinstance(data, list) else 1    
        frame = [self.FRAME_STX, self.FRAME_WRITE, reg, nb_data]

        # elementwise append
        if(nb_data > 1):
            frame = [*frame, *data]
        else:
            frame.append(data)

        # add the crc back
        frame.append(self.calc_crc(frame))

        # convert to byte array before we send to serial
        self.device.write(bytes(frame))

        # read back what we got...
        # format is [FRAME_STX, FRAME_WRITE, FRAME_ACK, CRC] (4 bytes)
        read_bytes = self.device.read(size=4)

        # check CRC against other bits
        if (self.calc_crc(read_bytes[0:-1]) != read_bytes[-1]):
            return False

        return (read_bytes[2] == self.FRAME_ACK)

    def read_frame_ack(self, reg, nb_data=1):
        frame = [self.FRAME_STX, self.FRAME_READ, reg, nb_data]
        # append crc to the end
        frame.append(self.calc_crc(frame))

        # request a read
        self.device.write(bytes(frame))
        read_bytes =self.device.read(size=3 + nb_data)
        return read_bytes[2:-1]

    def get_version(self):
        # we are only returning 1 byte, so unpack the array
        return int(self.read_frame_ack(self.REG_VERSION)[0])

    # Set liquid lens voltagez
    # 0x0000 (0)= 24 V
    # 0xB3B0 (46000) = 70 V
    def set_voltage(self, voltage):
        focus_lsb = voltage & 0x00FF
        focus_msb = (voltage >> 8)

        return self.write_frame_ack(self.REG_FOC_LSB, [focus_lsb, focus_msb])





