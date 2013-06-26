import logging, time, threading, copy
logging.basicConfig()

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import Log
from cfclient.utils.logconfigreader import LogVariable, LogConfig

from gameobjects.vector3 import *
from gameobjects.matrix44 import *
from math import radians

class Copter:
	def __init__(self):
		self.crazyflie = Crazyflie()
		cflib.crtp.init_drivers()

		self.targetParameters = {"forward_angle": 0, "left_angle": 0, "thrust_percentage": 0}
		self.currentParameters = {"pitch": 0, "roll": 0, "yaw": 0}
		self.frameOfReference = {"pitch": 0, "roll": 0, "yaw": 0}

	def connect(self):
		self.crazyflie.connectSetupFinished.add_callback(self.on_connection_established_with_copter)
		self.crazyflie.open_link("radio://0/10/250K")

	def on_connection_established_with_copter(self, uri):
		self.register_yaw_update_callback()
		thread = threading.Thread(target=self.continuously_update_parameters)
		thread.daemon = True
		thread.start()


	def record_frame_of_reference(self):
		self.frameOfReference = copy.deepcopy(self.currentParameters)

	def set_target_forward_angle(self, degrees):
		self.targetParameters["forward_angle"] = degrees

	def set_target_left_angle(self, degrees):
		self.targetParameters["left_angle"] = degrees

	def set_target_thrust_percentage(self, percentage):
		self.targetParameters["thrust_percentage"] = percentage


	def on_stabilizer_update(self, data):
		if "stabilizer.pitch" in data:
			self.currentParameters["pitch"] = data["stabilizer.pitch"]
		if "stabilizer.roll" in data:
			self.currentParameters["roll"] = data["stabilizer.roll"]
		if "stabilizer.yaw" in data:
			self.currentParameters["yaw"] = data["stabilizer.yaw"]

	def on_yaw_update_callback_failed(self):
		logger.warning("yaw callback failed")

	def register_yaw_update_callback(self):
		logconf = LogConfig("stabilizer", 10)
		logconf.addVariable(LogVariable("stabilizer.pitch", "float"))
		logconf.addVariable(LogVariable("stabilizer.roll", "float"))
		logconf.addVariable(LogVariable("stabilizer.yaw", "float"))
		self.logPacket = self.crazyflie.log.create_log_packet(logconf)
		if (self.logPacket is None):
			logger.warning("Could not setup logconfiguration after connection!")
			return

		self.logPacket.dataReceived.add_callback(self.on_stabilizer_update)
		self.logPacket.error.add_callback(self.on_yaw_update_callback_failed)
		self.logPacket.start()



	def get_current_flight_parameters(self):
		pitchTrim = -self.frameOfReference["pitch"]
		rollTrim = -self.frameOfReference["roll"]
		yawTrim = -self.frameOfReference["yaw"]

		targetTiltVector = Vector3(self.targetParameters["left_angle"], self.targetParameters["forward_angle"], 0.0)
		yawCorrectingRotation = Matrix44.z_rotation(radians(self.currentParameters["yaw"]+yawTrim))
		correctedVector = yawCorrectingRotation.transform(targetTiltVector)
		
		return {
			"pitch" : correctedVector[1] + pitchTrim,
			"roll" : correctedVector[0] + rollTrim,
			"thrust" : self.targetParameters["thrust_percentage"]*65365.0
		}

	def continuously_update_parameters(self):
		while True:
			flightParameters = self.get_current_flight_parameters()
			self.crazyflie.commander.send_setpoint(flightParameters["roll"], flightParameters["pitch"], 0, flightParameters["thrust"])
			time.sleep(0.1)