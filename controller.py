import json, threading
import tornado.ioloop, tornado.web, tornado.websocket
import copter

from gameobjects.vector3 import *
from gameobjects.matrix44 import *
from math import radians

class MobileController:
	def __init__(self):
		self.copter = copter.Copter()
		self.frameOfReference = {"roll":0, "pitch":0, "yaw":0}

		self.web_application = tornado.web.Application([
			(r"/ws", self.SocketHandler, dict(data = self)),
			(r"/rest/(.*)", self.RestHandler, dict(data = self)),
			(r"/(.*)", self.StaticHandler),
		])

	def run_async(self):
		thread = threading.Thread(target=self.run)
		thread.daemon = True
		thread.start()

	def run(self):
		self.web_application.listen(8080)
		tornado.ioloop.IOLoop.instance().start()

	class RestHandler(tornado.web.RequestHandler):
		def post(self, action):
			if(action == "establish_connection_with_copter"):
				self.controller.copter.record_frame_of_reference()
				self.controller.copter.connect()

		def initialize(self, data):
			self.controller = data


	class StaticHandler(tornado.web.RequestHandler):
		def get(self, file):
			if not file:
				file = "controller.html"

			try:
				self.write(open(file, 'r').read())
			except IOError:
				self.write("")

	class SocketHandler(tornado.websocket.WebSocketHandler):
		def open(self):
			print "Socket Opened"

		def initialize(self, data):
			self.controller = data

		def on_message(self, message):
			mobileParameters = json.loads(message)
			if "heading" in mobileParameters:
				heading = mobileParameters["heading"]
				self.controller.copter.set_target_forward_angle(heading["forward"])
				self.controller.copter.set_target_left_angle(heading["left"])

			if "thrust_percentage" in mobileParameters:
				self.controller.copter.set_target_thrust_percentage(mobileParameters["thrust_percentage"])

		def on_close(self):
			print "Socket Closed"

controller = MobileController()
controller.run_async()

raw_input("Press Enter to exit...")