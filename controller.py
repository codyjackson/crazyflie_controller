import logging
logging.basicConfig()

import sys
print sys.path

import json
import tornado.ioloop, tornado.web, tornado.websocket
import sys
import time
from threading import Thread

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import Log
from cfclient.utils.logconfigreader import LogVariable, LogConfig

from gameobjects.vector3 import *
from gameobjects.matrix44 import *
from math import radians

PHONE_PARAMETERS = {"roll":0.0, "pitch":0.0, "yaw":0.0, "thrust_percentage":0.0}
PHONE_ZERO_ORIENTATION = {"roll":0.0, "pitch":0.0, "yaw":0.0, "thrust_percentage":0.0}


class MainHandler(tornado.web.RequestHandler):
	def get(self):
		controllerHTML = open('controller.html', 'r').read()
		self.write(controllerHTML)

class SocketHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print "Socket Opened"

	def on_message(self, message):
		global PHONE_PARAMETERS
		phoneParams = json.loads(message)
		PHONE_PARAMETERS["roll"] = phoneParams["roll"]
		PHONE_PARAMETERS["pitch"] = phoneParams["pitch"]
		PHONE_PARAMETERS["yaw"] = phoneParams["yaw"]
		PHONE_PARAMETERS["thrust_percentage"] = phoneParams["thrust_percentage"]
		
		if "is_zero" in phoneParams:
			PHONE_ZERO_ORIENTATION = copy.deepcopy(PHONE_PARAMETERS)

	def on_close(self):
		print "Socket Closed"

application = tornado.web.Application([
	(r"/", MainHandler),
	(r"/ws", SocketHandler),
])

class Copter:
	def __init__(self):
		self.crazyflie = Crazyflie()
		cflib.crtp.init_drivers()

		self.crazyflie.connectSetupFinished.add_callback(self.OnConnectionEstablished)
		self.crazyflie.open_link("radio://0/10/250K")

		self.yaw = 0

	def OnYawChanged(self, data):
		if "stabilizer.yaw" not in data:
			return

		self.yaw = data["stabilizer.yaw"]

	def OnLoggingError(self):
		logger.warning("Callback of error in LogEntry :(")

	def RegisterLogCallbacks(self):
		logconf = LogConfig("stabilizer", 10)
		logconf.addVariable(LogVariable("stabilizer.yaw", "float"))
		self.logPacket = self.crazyflie.log.create_log_packet(logconf)
		if (self.logPacket is not None):
			self.logPacket.dataReceived.add_callback(self.OnYawChanged)
			self.logPacket.error.add_callback(self.OnLoggingError)
			self.logPacket.start()
			print "started"
		else:
			logger.warning("Could not setup logconfiguration after connection!")

	def StartWebServer(self):
		application.listen(8080)
		tornado.ioloop.IOLoop.instance().start()

	def OnConnectionEstablished(self, uri):
		print "connection established"

		self.RegisterLogCallbacks()
		Thread(target=self.Tick).start()
		Thread(target=self.StartWebServer).start()

	def GetOffsetOrientation(self, zeroOrientation, currentOrientation):
		offsetOrientation = {
			"roll" : currentOrientation["roll"] - zeroOrientation["roll"],
			"pitch" : currentOrientation["pitch"] - zeroOrientation["pitch"],
			"yaw" : currentOrientation["yaw"] - zeroOrientation["yaw"]
		}
		return offsetOrientation

	def Tick(self):
		global PHONE_PARAMETERS, PHONE_ZERO_ORIENTATION
		while True:
			phoneOffsetOrientation = self.GetOffsetOrientation(PHONE_ZERO_ORIENTATION, PHONE_PARAMETERS)
			phoneTiltVector = Vector3(phoneOffsetOrientation["roll"], phoneOffsetOrientation["pitch"], 0.0)
			rotationAmount = -self.yaw
			rotation = Matrix44.z_rotation(radians(-rotationAmount))
			orientationVector = rotation.transform(phoneTiltVector)
			self.crazyflie.commander.send_setpoint(orientationVector[0], orientationVector[1], 0, PHONE_PARAMETERS["thrust_percentage"]*65365.0)
			time.sleep(0.01)

copter = Copter()
