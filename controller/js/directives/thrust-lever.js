application.directive("thrustLever", function(){
	return {
		restrict: 'E',
		template: '<div class="panel" style="position:relative"><div class="handle" style="position:absolute;left:0;"></div></div>',
		replace: true,
		link: function(scope, element, attributes){
			var panel = $(element);
			var handle = panel.find('.handle');

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

			var isHolding = false;
			element.mouseenter(function(ev){
				if(isHolding && !ev.which)
					isHolding = false;
			});
			element.mousedown(function(ev){
				isHolding = true;
				update_lever_position(ev.clientX);
			});
			element.mousemove(function(ev){
				if(isHolding)
					update_lever_position(ev.clientX);
			});
			element.mouseup(function(){
				isHolding = false;
			});
		}
	};
});