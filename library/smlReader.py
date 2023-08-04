
import logging
import time
import json
import serial
from smllib import SmlStreamReader
#from .const import UNITS, OBIS_NAMES

from typing import Union

UNITS = {
    1: 'a',
    2: 'mo',
    3: 'wk',
    4: 'd',
    5: 'h',
    6: 'min',
    7: 's',
    8: '°',
    9: '°C',
    10: 'currency',
    11: 'm',
    12: 'm/s',
    13: 'm³',
    14: 'm³',
    15: 'm³/h',
    16: 'm³/h',
    17: 'm³/d',
    18: 'm³/d',
    19: 'l',
    20: 'kg',
    21: 'N',
    22: 'Nm',
    23: 'Pa',
    24: 'bar',
    25: 'J',
    26: 'J/h',
    27: 'W',
    28: 'VA',
    29: 'var',
    30: 'Wh',
    31: 'VAh',
    32: 'varh',
    33: 'A',
    34: 'C',
    35: 'V',
    36: 'V/m',
    37: 'F',
    38: 'Ω',
    39: 'Ωm²/m',
    40: 'Wb',
    41: 'T',
    42: 'A/m',
    43: 'H',
    44: 'Hz',
    45: '1/(Wh)',
    46: '1/(varh)',
    47: '1/(VAh)',
    48: 'V²h',
    49: 'A²h',
    50: 'kg/s',
    51: 'S',
    52: 'K',
    53: '1/(V²h)',
    54: '1/(A²h)',
    55: '1/m³',
    56: '%',
    57: 'Ah',
    60: 'Wh/m³',
    61: 'J/m³',
    62: 'Mol%',
    63: 'g/m³',
    64: 'Pas',
    65: 'J/kg',
    66: 'g/cm²',
    67: 'arm',
    70: 'dBm',
    71: 'dBµV',
    72: 'dB',
}

# https://www.promotic.eu/en/pmdoc/Subsystems/Comm/PmDrivers/IEC62056_OBIS.htm
OBIS_NAMES = {
    '0100000009ff': 'Geräteeinzelidentifikation',
    '0100010800ff': 'Zählerstand Total',
    '0100010801ff': 'Zählerstand Tarif 1',
    '0100010802ff': 'Zählerstand Tarif 2',
    '0100011100ff': 'Total-Zählerstand',
    '0100020800ff': 'Wirkenergie Total',
    '0100100700ff': 'aktuelle Wirkleistung',
    '0100170700ff': 'Momentanblindleistung L1',
    '01001f0700ff': 'Strom L1',
    '0100200700ff': 'Spannung L1',
    '0100240700ff': 'Wirkleistung L1',
    '01002b0700ff': 'Momentanblindleistung L2',
    '0100330700ff': 'Strom L2',
    '0100340700ff': 'Spannung L2',
    '0100380700ff': 'Wirkleistung L2',
    '01003f0700ff': 'Momentanblindleistung L3',
    '0100470700ff': 'Strom L3',
    '0100480700ff': 'Spannung L3',
    '01004c0700ff': 'Wirkleistung L3',
    '0100510701ff': 'Phasenabweichung Spannungen L1/L2',
    '0100510702ff': 'Phasenabweichung Spannungen L1/L3',
    '0100510704ff': 'Phasenabweichung Strom/Spannung L1',
    '010051070fff': 'Phasenabweichung Strom/Spannung L2',
    '010051071aff': 'Phasenabweichung Strom/Spannung L3',
    '010060320002': 'Aktuelle Chiptemperatur',
    '010060320003': 'Minimale Chiptemperatur',
    '010060320004': 'Maximale Chiptemperatur',
    '010060320005': 'Gemittelte Chiptemperatur',
    '010060320303': 'Spannungsminimum',
    '010060320304': 'Spannungsmaximum',
    '01000e0700ff': 'Netz Frequenz',
    '8181c78203ff': 'Hersteller-Identifikation',
    '8181c78205ff': 'Öffentlicher Schlüssel',
}

CRC16_X25_TABLE = (
    0x0000, 0x1189, 0x2312, 0x329B, 0x4624, 0x57AD, 0x6536, 0x74BF,
    0x8C48, 0x9DC1, 0xAF5A, 0xBED3, 0xCA6C, 0xDBE5, 0xE97E, 0xF8F7,
    0x1081, 0x0108, 0x3393, 0x221A, 0x56A5, 0x472C, 0x75B7, 0x643E,
    0x9CC9, 0x8D40, 0xBFDB, 0xAE52, 0xDAED, 0xCB64, 0xF9FF, 0xE876,
    0x2102, 0x308B, 0x0210, 0x1399, 0x6726, 0x76AF, 0x4434, 0x55BD,
    0xAD4A, 0xBCC3, 0x8E58, 0x9FD1, 0xEB6E, 0xFAE7, 0xC87C, 0xD9F5,
    0x3183, 0x200A, 0x1291, 0x0318, 0x77A7, 0x662E, 0x54B5, 0x453C,
    0xBDCB, 0xAC42, 0x9ED9, 0x8F50, 0xFBEF, 0xEA66, 0xD8FD, 0xC974,
    0x4204, 0x538D, 0x6116, 0x709F, 0x0420, 0x15A9, 0x2732, 0x36BB,
    0xCE4C, 0xDFC5, 0xED5E, 0xFCD7, 0x8868, 0x99E1, 0xAB7A, 0xBAF3,
    0x5285, 0x430C, 0x7197, 0x601E, 0x14A1, 0x0528, 0x37B3, 0x263A,
    0xDECD, 0xCF44, 0xFDDF, 0xEC56, 0x98E9, 0x8960, 0xBBFB, 0xAA72,
    0x6306, 0x728F, 0x4014, 0x519D, 0x2522, 0x34AB, 0x0630, 0x17B9,
    0xEF4E, 0xFEC7, 0xCC5C, 0xDDD5, 0xA96A, 0xB8E3, 0x8A78, 0x9BF1,
    0x7387, 0x620E, 0x5095, 0x411C, 0x35A3, 0x242A, 0x16B1, 0x0738,
    0xFFCF, 0xEE46, 0xDCDD, 0xCD54, 0xB9EB, 0xA862, 0x9AF9, 0x8B70,
    0x8408, 0x9581, 0xA71A, 0xB693, 0xC22C, 0xD3A5, 0xE13E, 0xF0B7,
    0x0840, 0x19C9, 0x2B52, 0x3ADB, 0x4E64, 0x5FED, 0x6D76, 0x7CFF,
    0x9489, 0x8500, 0xB79B, 0xA612, 0xD2AD, 0xC324, 0xF1BF, 0xE036,
    0x18C1, 0x0948, 0x3BD3, 0x2A5A, 0x5EE5, 0x4F6C, 0x7DF7, 0x6C7E,
    0xA50A, 0xB483, 0x8618, 0x9791, 0xE32E, 0xF2A7, 0xC03C, 0xD1B5,
    0x2942, 0x38CB, 0x0A50, 0x1BD9, 0x6F66, 0x7EEF, 0x4C74, 0x5DFD,
    0xB58B, 0xA402, 0x9699, 0x8710, 0xF3AF, 0xE226, 0xD0BD, 0xC134,
    0x39C3, 0x284A, 0x1AD1, 0x0B58, 0x7FE7, 0x6E6E, 0x5CF5, 0x4D7C,
    0xC60C, 0xD785, 0xE51E, 0xF497, 0x8028, 0x91A1, 0xA33A, 0xB2B3,
    0x4A44, 0x5BCD, 0x6956, 0x78DF, 0x0C60, 0x1DE9, 0x2F72, 0x3EFB,
    0xD68D, 0xC704, 0xF59F, 0xE416, 0x90A9, 0x8120, 0xB3BB, 0xA232,
    0x5AC5, 0x4B4C, 0x79D7, 0x685E, 0x1CE1, 0x0D68, 0x3FF3, 0x2E7A,
    0xE70E, 0xF687, 0xC41C, 0xD595, 0xA12A, 0xB0A3, 0x8238, 0x93B1,
    0x6B46, 0x7ACF, 0x4854, 0x59DD, 0x2D62, 0x3CEB, 0x0E70, 0x1FF9,
    0xF78F, 0xE606, 0xD49D, 0xC514, 0xB1AB, 0xA022, 0x92B9, 0x8330,
    0x7BC7, 0x6A4E, 0x58D5, 0x495C, 0x3DE3, 0x2C6A, 0x1EF1, 0x0F78
)


def get_crc(buf: Union[memoryview, bytes]) -> int:
    crc = 0xffff
    for byte in buf:
        crc = CRC16_X25_TABLE[(byte ^ crc) & 0xff] ^ (crc >> 8 & 0xff)
    crc ^= 0xffff
    return (crc & 0xFF) << 8 | crc >> 8

SML_START = b'\x1b\x1b\x1b\x1b\x01\x01\x01\x01'
SML_END = b'\x1b\x1b\x1b\x1b\x1a'
#startMessage = b'\x01\x01\x01\x01'
#escapeSequence = b'\x1b\x1b\x1b\x1b'

class SmlReader(object):

    def __init__(self,device,baudrate=9600,logger='SML2MQTT'):

        _libName = str(__name__.rsplit('.', 1)[-1])
        self._log = logging.getLogger(logger + '.' + _libName + '.' + self.__class__.__name__)

        self._log.debug('Create MQTT mqttclient Object')

        self._device = device
        self._baudrate = baudrate

        'https://github.com/Ixtalo/SmlMqttProcessor/blob/master/attic/smlmqttprocessor.py'

    def __del__(self):
        self._log.info('Destroy may self')

    def connect(self):
        # PySerial
        self._serial = serial.Serial(port = self._device,
                                     baudrate = self._baudrate,
                                     parity = serial.PARITY_NONE,
                                     stopbits=serial.STOPBITS_ONE,
                                     bytesize=serial.EIGHTBITS,
                                     timeout=1.0)

        self._log.info("Serial port: %s", str(self._serial))
       # self._serial.close()
       # print(self._serial)

    def close(self):
        self._log.info('Close serial port')
        self._serial.close()

    def read(self):
       # time.sleep(0.5)
       # self._serial.open()
        #self._serial.reset_input_buffer()
        #self._serial.reset_output_buffer()

      #  print('---READ---')
        #buffer = self._serial.read(400)

        buffer = ''
      #  print(self._serial.in_waiting)
        try:
            buffer = self._serial.read()  # Wait forever for anything
            time.sleep(1)  # Sleep (or inWaiting() doesn't give the correct value)
            data_left = self._serial.in_waiting  # Get the number of characters ready to be read
       # print(data_left)
            buffer += self._serial.read(data_left)
        except:
            print('Failed')
            return False
       # if (self._serial.in_waiting > 0 ):
        #    while self._serial.in_waiting > 0:
          #  print('read')
         #       buffer = self._serial.read(400)
         #   print(len(buffer))
          #  print(buffer)

        if (SML_START in buffer and SML_END in buffer):
        #    print('Valid Frame')
            p0, p1 = buffer.index(SML_START), buffer.index(SML_END)
         #   print('P0', p0)
          #  print('P1', p1)
            crc_msg = buffer[-2] << 8 | buffer[-1]
            crc_calc = get_crc(buffer[:-2])
            if crc_msg != crc_calc:
                self._log.error('CRC failure')
           #     print('CRC Error')
               # raise CrcError(msg, crc_msg, crc_calc)
            else:
                self._log.info('Good frame')
            #    print('crc Ok')
             #   print(p0 + p1 + len(SML_END) + 3)
                return buffer[p0:p0 + p1 + len(SML_END) + 3]

          #  x = buffer.endswith(SML_END)
           # print('x', x)
           # y = buffer.startswith(SML_START)
           # print('y', y)
           #buffer = self._serial.read_until(SML_END)
      #  self._serial.close()
       # print(buffer)
      #  print(len(buffer))
      #  print(buffer)

        return False


    def pars1(self,data):
        _store = {}

        stream = SmlStreamReader()
        stream.add(data)
        sml_frame = stream.get_frame()
        if sml_frame is None:
        #    print('Bytes missing')
            self._log.error('Byetes missing')

        # Shortcut to extract all values without parsing the whole frame
        obis_values = sml_frame.get_obis()

        for list_entry in obis_values:
            _localStore = {}

            _localStore['data_value'] = list_entry.get_value()
            _localStore['data_unit'] = UNITS.get(list_entry.unit,None)
            _localStore['data_type'] =  OBIS_NAMES.get(list_entry.obis,None)
            _store[list_entry.obis.obis_short] = _localStore
           # print('-----')
          #  print(list_entry)
           # print(list_entry.obis)  # 0100010800ff
            #print(list_entry.obis.obis_code)  # 1-0:1.8.0*255
           # print(list_entry.obis.obis_short)  # 1.8.0
          #  print(list.entry.obis.values)
            #print(list_entry.format_msg())
           # print('Values',list_entry.get_value())
           # print('Print Units',list_entry.unit)
            #print(UNITS.get(list_entry.unit,None))
            #print(OBIS_NAMES.get(list_entry.obis,None))

        return json.dumps(_store)




if __name__ == '__main__':
    s = SmlReader('/dev/ttyUSB0')
    s.connect()
    while True:
        x = s.read()
        print(x)
        if not x == False:
            print('Raw Frem',x)
            s.pars1(x)
        else:
            print('Failed')
            time.sleep(0.5)