application.directive("thrustLever", ["$timeout", function($timeout){
	return {
		restrict: 'E',
		template: '<div class="panel" style="position:relative"><div class="handle" style="position:absolute;left:0;"></div></div>',
		replace: true,
		link: function(scope, element, attributes){
			var panel = $(element);
			var handle = panel.find('.handle');

			function get_percentage_of_x_position_on_panel(x){
				var maxX = panel.outerWidth()-handle.outerWidth();
				return x/maxX;
			}

			function get_thrust_percentage(){
				return get_percentage_of_x_position_on_panel(handle.offset().left);
			}

			function move_lever(percentage){
				if(percentage < 0 || percentage > 1)
					throw "percentage must be between 0.0 and 1.0."
				var maxX = panel.outerWidth()-handle.outerWidth();
				var x = maxX*percentage;
				handle.offset({left:x, top:handle.outerWidth().top});
			}

			var isHandleHeld = false;
			(function decay_thrust(){
				if(attributes.decayRate && !isHandleHeld){
					var newPercentage = get_thrust_percentage() - (attributes.decayRate)/250;
					if(newPercentage < 0)
						newPercentage = 0;

					move_lever(newPercentage);
				}
				$timeout(decay_thrust, 4, false);
			})();
				
			function update_lever_position(mouseRelativeX){
				var handleHalfWidth = handle.outerWidth()/2.0;
				var percentage = (mouseRelativeX-handleHalfWidth)/panel.outerWidth();

				var maxX = panel.outerWidth()-handle.outerWidth();
				var handlePosition = handle.offset();
				var targetX = panel.outerWidth() * percentage;

				var left = targetX <= maxX ? targetX : maxX;
				left = left >= 0 ? left : 0;
				handle.offset({left:left, top:handlePosition.top});
			}

			element.mouseenter(function(ev){
				if(isHandleHeld && !ev.which)
					isHandleHeld = false;
			});
			element.mousedown(function(ev){
				isHandleHeld = true;
				update_lever_position(ev.clientX);
			});
			element.mousemove(function(ev){
				if(isHandleHeld)
					update_lever_position(ev.clientX);
			});
			element.mouseup(function(){
				isHandleHeld = false;
			});
		}
	};
}]);