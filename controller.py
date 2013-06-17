import json, threading
import tornado.ioloop, tornado.web, tornado.websocket
import copter

class MobileController:
	def __init__(self):
		self.web_application = tornado.web.Application([
			(r"/", self.MainHandler),
			(r"/ws", self.SocketHandler, dict(data = copter.Copter())),
		])

	def run_async(self):
		threading.Thread(target=self.run).start()

	def run(self):
		self.web_application.listen(8080)
		tornado.ioloop.IOLoop.instance().start()

	class MainHandler(tornado.web.RequestHandler):
		def get(self):
			controllerHTML = open('controller.html', 'r').read()
			self.write(controllerHTML)

	class SocketHandler(tornado.websocket.WebSocketHandler):
		def open(self):
			print "Socket Opened"

		def initialize(self, data):
			self.copter = data
			self.parameterFrameOfReference = {}

		def on_message(self, message):
			phoneParameters = json.loads(message)
			if len(self.parameterFrameOfReference) == 0:
				self.parameterFrameOfReference = phoneParameters
				self.copter.connect()

			self.copter.set_target_forward_angle(phoneParameters["pitch"] - self.parameterFrameOfReference["pitch"])
			self.copter.set_target_left_angle(phoneParameters["roll"] - self.parameterFrameOfReference["roll"])
			self.copter.set_target_thrust_percentage(phoneParameters["thrust_percentage"] - self.parameterFrameOfReference["thrust_percentage"])

		def on_close(self):
			print "Socket Closed"

controller = MobileController()
controller.run_async()
