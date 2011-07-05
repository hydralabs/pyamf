/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.ohloh
{
	import flash.events.AsyncErrorEvent;
	import flash.events.Event;
	import flash.events.EventDispatcher;
	import flash.events.NetStatusEvent;
	import flash.events.SecurityErrorEvent;
	import flash.net.NetConnection;
	import flash.net.Responder;
	
	import mx.controls.Alert;
	import mx.utils.ObjectUtil;
	
	[Event(name="response", type="flash.events.Event")]
	[Event(name="error", type="flash.events.Event")]
	
	/**
	 * This is an example of using the Ohloh API from Actionscript 3.0.
	 * 
	 * It retrieves an account and shows the profile associated.
	 * 
     * Detailed information can be found at the Ohloh website:
     * 
	 * @see http://www.ohloh.net/api
	 */	
	public class ApiExample extends EventDispatcher
	{
		public static const RESPONSE:	String = "response";
		public static const ERROR:		String = "error";
		
		private var userEmail: 			String;
		private var gateway:			NetConnection;
		
		public var info:				XMLList;
		
		public function ApiExample( userEmail:String )
		{
			super();
			
			this.userEmail = userEmail;
		}
		
		public function connect( host:String ):void
	    {
	    	gateway = new NetConnection();
	    	gateway.addEventListener( NetStatusEvent.NET_STATUS, onFault );
			gateway.addEventListener( AsyncErrorEvent.ASYNC_ERROR, onFault );
			gateway.addEventListener( SecurityErrorEvent.SECURITY_ERROR, onFault );
	    	gateway.connect(host);
	    	
	    	var responder:Responder = new Responder( onResult, onFault );
	    	gateway.call( 'ohloh.account', responder, userEmail );
	    }
	    
	    private function onFault( event:* ):void
	    {
	    	Alert.show( ObjectUtil.toString(event), 'Connection Error' );
	    	
	    	dispatchEvent( new Event(ERROR) );
	    }
	    
	    private function onResult(event:*):void
	    {
			info = new XMLList(event).result.account;
			
	    	dispatchEvent( new Event(RESPONSE) );
	    }
	    
	}
}