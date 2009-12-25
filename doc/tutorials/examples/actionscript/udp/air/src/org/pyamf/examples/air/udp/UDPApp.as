package org.pyamf.examples.air.udp
{
	import flash.events.Event;
	
	import mx.controls.TextArea;
	import mx.core.ScrollPolicy;
	import mx.core.WindowedApplication;
	import mx.events.AIREvent;
	import mx.events.FlexEvent;
	
	import org.pyamf.examples.air.udp.events.LogEvent;
	import org.pyamf.examples.air.udp.net.NetworkInfoSupport;
	import org.pyamf.examples.air.udp.net.UDPSupport;

	public class UDPApp extends WindowedApplication
	{
		private var server				: UDPSupport;
		private var network				: NetworkInfoSupport;
		private var evt					: LogEvent;
		
		private static var output		: TextArea;
		
		/**
		 * Constructor.
		 */		
		public function UDPApp()
		{
			super();
			
			verticalScrollPolicy = ScrollPolicy.OFF;
			horizontalScrollPolicy = ScrollPolicy.OFF;
			
			addEventListener(AIREvent.WINDOW_COMPLETE, onWindowComplete,
							 false, 0, true);
		}
		
		private function onWindowComplete( event:AIREvent ) : void
		{
			removeEventListener(event.type, onWindowComplete);
			
			// UI
			output = new TextArea();
			output.editable = false;
			output.width = stage.stageWidth;
			output.height = stage.stageHeight - 10;
			output.setStyle("fontFamily", "Arial");
			output.setStyle("fontSize", 11);
			output.setStyle("color", "white");
			output.setStyle("backgroundColor", "black");
			output.setStyle("textIndent", 5);
			output.addEventListener(FlexEvent.VALUE_COMMIT, onScrollUpdate,
									false, 0, true);
			addChild( output );
			
			// get local network info
			network = new NetworkInfoSupport();
			network.addEventListener(LogEvent.UPDATE, log, false, 0, true);
			network.addEventListener(Event.NETWORK_CHANGE, onNetworkChange,
									 false, 0, true);
			
			try
			{
				// connect to udp server
				server = new UDPSupport(network.activeAddress);
				server.addEventListener(LogEvent.UPDATE, log, false, 0, true);
				server.connect();
			}
			catch( e:Error )
			{
				evt = new LogEvent( LogEvent.UPDATE, e.toString() );
				log( evt );
			}
			
		}
		
		private function onNetworkChange( event:Event ) : void
		{
			evt = new LogEvent( LogEvent.UPDATE, event.toString() );
			log( evt );
		}
		
		private function onScrollUpdate( event:FlexEvent ):void
		{
			output.verticalScrollPosition = output.maxVerticalScrollPosition;
		}
		
		private static function log( event:LogEvent ) : void
		{
			output.text += event.message;
			trace(event.message);
		}
		
	}
}