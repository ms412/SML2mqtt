#!/usr/bin/python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


__app__ = "SML2mqtt"
__VERSION__ = "0.1"
__DATE__ = "20.05.2023"
__author__ = "Markus Schiesser"
__contact__ = "M.Schiesser@gmail.com"
__copyright__ = "Copyright (C) 2023 Markus Schiesser"
__license__ = 'GPL v3'

import sys
import os
import time
import json
import logging
from configobj import ConfigObj
from library.smlReader import SmlReader
from library.mqttclientV2 import mqttclient
from library.logger import loghandler


class Sml2mqtt(object):

    def __init__(self, configfile='sml2mqtt.config'):
        #    threading.Thread.__init__(self)

        self._configfile = os.path.join(os.path.dirname(__file__), configfile)
       # print(self._configfile)

        self._configBroker = None
        self._configLog = None
        self._configInput = None
        self._configOutput = None

        self._mqtt = None
        self._sml = None

        self._rootLoggerName = ''

    def readConfig(self):

        _config = ConfigObj(self._configfile)

        if bool(_config) is False:
            print('ERROR config file not found', self._configfile)
            sys.exit()
            # exit

        self._BrokerConfig = _config.get('BROKER', None)
        self._LoggerConfig = _config.get('LOGGING', None)
        self._SmlConfig = _config.get('SML', None)
        return True

    def startLogger(self):
        # self._log = loghandler('marantec')

        self._LoggerConfig['DIRECTORY'] = os.path.dirname(__file__)
        print(self._LoggerConfig)
        self._root_logger = loghandler(self._LoggerConfig.get('NAME', 'SML2MQTT'))
        self._root_logger.handle(self._LoggerConfig.get('LOGMODE', 'PRINT'), self._LoggerConfig)
        self._root_logger.level(self._LoggerConfig.get('LOGLEVEL', 'DEBUG'))
        self._rootLoggerName = self._LoggerConfig.get('NAME', self.__class__.__name__)
        print(self._LoggerConfig)
        self._log = logging.getLogger(self._rootLoggerName + '.' + self.__class__.__name__)

        self._log.info('Start %s, %s' % (__app__, __VERSION__))

        return True

    def startMqttBroker(self):
        self._log.debug('Methode: startMqtt()')
        self._mqtt = mqttclient(self._rootLoggerName)

        _host = self._BrokerConfig.get('HOST', 'localhost')
        _port = self._BrokerConfig.get('PORT', 1883)

        _state = False
        while not _state:
            _state = self._mqtt.connect(_host, _port)
            if not _state:
                self._log.error('Failed to connect to broker: %s', _host)
                time.sleep(5)

        self._log.debug('Sucessful connect to broker: %s', _host)

        return True

    def publishUpdate(self,data):
        self._log.debug('Send Update State')
        _topic = self._BrokerConfig.get('PUBLISH','/SMARTHOME/DEFAULT')

       # _topic = _configTopic + '/' + 'SYSTEM_STATE'
        #self._log.info('SYSTEM_STATE: %s'%(self._systemState))
        self._mqtt.publish(_topic, data)

        return True

    def startSML(self):
        self._log.debug('Methode: startSML()')
        self._sml = SmlReader(self._SmlConfig.get('SERIAL','/dev/ttyUSB0'))
        return True
    
    def stopSML(self):
        self._log.debug('Methode: stopSML()')
        del self._sml
        return True

    def getData(self):

        self._sml.connect()
       # while True:
        _serialData = self._sml.read()
       # print(x)
        if not _serialData == False:
        #    print('Raw Frem', x)
            self._log.debug('Data from serial port: %s',_serialData)
            _smlData= self._sml.pars1(_serialData)
            self.publishUpdate(_smlData)
            self._sml.close()
            return(True)
        else:
            self._log.error('No Data at serial port')
         #   print('Failed')
            self._sml.close()
            time.sleep(2)
            return False


    def start(self):
        self.readConfig()
        self.startLogger()
        self.startMqttBroker()
        self.startSML()
        while (True):
            self.getData()
            self.stopSML()
            time.sleep(15)
            self.startSML()

if __name__ == "__main__":
    if len(sys.argv) == 2:
        configfile = sys.argv[1]
    else:
        configfile = './sml2mqtt.config'

    sg = Sml2mqtt(configfile)
    sg.start()