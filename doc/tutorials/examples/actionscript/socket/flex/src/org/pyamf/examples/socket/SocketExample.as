/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.socket
{
	import flash.events.Event;
	
	import mx.events.FlexEvent;
	
	import spark.components.Application;
	import spark.components.Button;
	
	/**
	 * This examples shows how to use Socket class in ActionScript 3,
	 * that allows you to make socket connections and to read and write
	 * raw binary data.
	 */
	public class SocketExample extends Application
	{
		public var start_btn	: Button;
		public var stop_btn		: Button;
		
		private var _server		: PythonSocket;
		
		[Bindable]
		public var log			: String;
		
		public function SocketExample()
		{
			super();
			
			addEventListener( FlexEvent.APPLICATION_COMPLETE, initApp );
		}
		
		private function initApp(event:FlexEvent):void
		{
			// Connect to server
			_server = new PythonSocket();
			
			// Listen for log updates
			_server.addEventListener( PythonSocket.CONNECTED, startState );
			_server.addEventListener( PythonSocket.DISCONNECTED, startState );
			_server.addEventListener( PythonSocket.LOG_UPDATE, logUpdate );
		}
		
		private function logUpdate( event:Event ):void
		{
			// Display log
			log = _server.log;
		}
		
		public function startFeed():void
		{
			stopState();
			
			// Start feed
			_server.write( "start" );
		}
		
		public function stopFeed():void
		{
			startState();
			
			// Stop feed
			_server.write( "stop" );
		}
		
		private function startState( event:Event=null ):void
		{
			start_btn.enabled = true;
			stop_btn.enabled = false;
		}
		
		private function stopState( event:Event=null ):void
		{
			start_btn.enabled = false;
			stop_btn.enabled = true;
		}
		
	}
}