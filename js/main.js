function radians(degrees){
	return degrees*Math.PI/180.0;
}

function Phone(){
	this.attitude = {
		"yaw" : 0,
		"pitch" : 0,
		"roll" : 0
	};
	this.attitude_frame_of_reference = $.extend({}, this.attitude);

	this.thrust_percentage = 0;

	this.on_new_attitude = function(event){
		this.attitude.yaw = event.alpha;
		//This defines pitch as positive when the top of the phone is tilted forward.
		this.attitude.pitch = -event.beta;
		this.attitude.roll = event.gamma;
	};

	this.on_record_attitude_frame_of_reference = function(event){
		this.attitude_frame_of_reference = $.extend({}, this.attitude);
	};

	this.get_relative_yaw = function(){
		var relativeYaw = this.attitude.yaw - this.attitude_frame_of_reference.yaw;
		if(relativeYaw < 0)
			relativeYaw += 360;
		return relativeYaw;
	};

	this.get_attitude_relative_to_frame_of_reference = function(){
		return {
			"yaw" : this.get_relative_yaw(),
			"pitch" : this.attitude.pitch - this.attitude_frame_of_reference.pitch,
			"roll" : this.attitude.roll - this.attitude_frame_of_reference.roll
		};
	};

	this.get_heading = function(){
		var	relativeAttitude = this.get_attitude_relative_to_frame_of_reference();
		//The division is used to reduce sensitivity.
		var uncorrectedHeading = $V([relativeAttitude.roll/2.0, relativeAttitude.pitch/2.0, 0]);
		var yawRotation = Matrix.RotationZ(radians(relativeAttitude.yaw));
		var correctedHeading = yawRotation.multiply(uncorrectedHeading);
		var components = correctedHeading.elements;

		return {
			"forward":components[1],
			"left":components[0]
		};
	};

	this.on_new_thrust_percentage = function(event){
		var touchTargets = event.targetTouches;
		if((touchTargets.length != 1) || (touchTargets[0].target.id !== 'thrust-input'))
		{
			this.thrust_percentage = 0;
			return;
		}

		event.preventDefault();

		var touch = event.targetTouches[0];
		var touchX = touch.clientX;
		var width = document.width;
		
		this.thrust_percentage = (1.0-((width - touchX)/width));
	};

	this.get_thrust_percentage = function(){
		return this.thrust_percentage;
	}
}

function load(){
	var connection = new WebSocket(document.URL.replace('http', 'ws')+'ws');
	var phone = new Phone();

	connection.onopen = function(){
		window.addEventListener("deviceorientation", function(event){
			phone.on_new_attitude(event);
			connection.send(JSON.stringify({heading:phone.get_heading()}));
		});

		function on_new_thrust_percentage(event){
			phone.on_new_thrust_percentage(event);
			connection.send(JSON.stringify({thrust_percentage:phone.get_thrust_percentage()}));
		}
		window.addEventListener("touchstart", on_new_thrust_percentage);
		window.addEventListener("touchend", on_new_thrust_percentage);
		window.addEventListener("touchmove", on_new_thrust_percentage);

		document.getElementById('record-frame-of-reference').onclick = function(){
			phone.on_record_attitude_frame_of_reference();
			$.post('rest/establish_connection_with_copter');
		};

		window.onbeforeunload = connection.close;
	};

	connection.onerror = function(error){
		console.log("fail" +error);
	};

	connection.onmessage = function(response){
		console.log(response.data);
	}
}