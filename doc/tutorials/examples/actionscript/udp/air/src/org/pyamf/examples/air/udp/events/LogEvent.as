package org.pyamf.examples.air.udp.events
{
	import flash.events.Event;

	public class LogEvent extends Event
	{
		public static const UPDATE : String = "update";
		
		private var _msg			: String;
		
		public function get message() : String
		{
			return _msg;
		}
		
		/**
		 * Constructor.
		 *  
		 * @param type
		 * @param message
		 * @param bubbles
		 * @param cancelable
		 */		
		public function LogEvent( type:String, message:String, bubbles:Boolean=false,
								  cancelable:Boolean=false )
		{
			super(type, bubbles, cancelable);
			
			_msg = message;
		}
		
	}
}