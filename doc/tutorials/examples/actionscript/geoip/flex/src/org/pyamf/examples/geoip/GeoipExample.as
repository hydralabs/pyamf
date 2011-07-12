/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
 */
package org.pyamf.examples.geoip
{
	import flash.events.NetStatusEvent;
	import flash.events.SecurityErrorEvent;
	import flash.net.NetConnection;
	import flash.net.Responder;
	
	import mx.controls.Alert;
	import mx.controls.SWFLoader;
	import mx.events.FlexEvent;
	
	import org.pyamf.examples.geoip.vo.GeoInfo;
	
	import spark.components.Application;
	import spark.components.RichEditableText;

	/**
	 * This examples shows how to use the GeoIP Python API
	 * with Flex and PyAMF.
	 * 
	 * @since 0.1
	 */
	public class GeoipExample extends Application
	{
		public var cc_txt			: RichEditableText;
		public var status_txt		: RichEditableText;
		public var flag				: SWFLoader;
		
		private var _gateway		: NetConnection;
		private var _status			: String;
		private var _myComputer		: GeoInfo;
		private var _countryCode	: String;
		private var _flag			: String;
		
		public function GeoipExample()
		{
			super();
			
			_flag = "unknown";
			
			addEventListener(FlexEvent.APPLICATION_COMPLETE, onInitApp);
		}
		
		private function onInitApp(event:FlexEvent): void
		{
			// setup connection
            _gateway = new NetConnection();
            _gateway.addEventListener(NetStatusEvent.NET_STATUS, onNetstatusError);
			_gateway.addEventListener(SecurityErrorEvent.SECURITY_ERROR, securityError);
			
            // Connect to gateway
            _gateway.connect("http://localhost:8000");
            
            // Set responder property to the object and methods that will receive the 
            // result or fault condition that the service returns.
            var responder:Responder = new Responder( onGeoInfoResult, onFault );
            
            // Call remote service to fetch geolocation data
            _gateway.call("geoip.getGeoInfo", responder);
            status_txt.text = "Loading...";
		}
		
		private function onGeoInfoResult(result:*): void
        {
        	_myComputer = result as GeoInfo;
        	
           	setInfo();
        }
        
        private function onNetstatusError(event:NetStatusEvent): void
        {
        	setInfo(event.info.code);
        }
		
		private function securityError(event:SecurityErrorEvent): void
		{
			setInfo(event.text);
		}
		
        private function setInfo(errorText:String=""): void
        {
        	if (errorText.length == 0) {
        		if ( _myComputer.country.code != null ) {
	           		 _countryCode = _myComputer.country.code;
	           		 cc_txt.text = _countryCode;
	           		 _status = _myComputer.country.name + " (" + _myComputer.ip + ")";
	           		 _flag = _countryCode.toLowerCase();
	           	} else {
	           		_status = "Unknown Location";
	           		cc_txt.text = _myComputer.ip;
	           		cc_txt.setStyle('fontSize', 10);
	           	}
        	} else {
        		cc_txt.text = "Error!";
        		_status = errorText;
        	}
        	
        	status_txt.text = _status;
        	flag.source = 'http://www.comp.nus.edu.sg/icons/awstats/flags/' + _flag + '.png';
        }
        
        private function onFault( error:* ): void
        {
            // notify the user of the problem
            var errorStr:String = "";
            for (var d:String in error) {
               errorStr += error[d] + "\n";
            }
            
            mx.controls.Alert.show(errorStr, "Remoting error");
        }
		
	}
}