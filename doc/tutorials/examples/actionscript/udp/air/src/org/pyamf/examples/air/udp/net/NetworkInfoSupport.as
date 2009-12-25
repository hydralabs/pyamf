package org.pyamf.examples.air.udp.net
{
	import __AS3__.vec.Vector;
	
	import flash.events.Event;
	import flash.events.EventDispatcher;
	import flash.net.InterfaceAddress;
	import flash.net.NetworkInfo;
	import flash.net.NetworkInterface;
	
	import org.pyamf.examples.air.udp.events.LogEvent;
	
	public class NetworkInfoSupport extends EventDispatcher
	{
		private var _info		: NetworkInfo;
		private var _interfaces	: Vector.<NetworkInterface>;
		
		/**
		 * Get active and inactive interfaces from this machine.
		 *  
		 * @return Vector of NetworkInterfaces
		 */		
		public function get interfaces() : Vector.<NetworkInterface>
		{
			return _interfaces;
		}
		
		/**
		 * Get all active interfaces.
		 *  
		 * @return Vector of NetworkInterfaces
		 */		
		public function get activeInterfaces() : Vector.<NetworkInterface>
		{
			var active:Vector.<NetworkInterface> = new Vector.<NetworkInterface>();
			
			for each ( var inet:NetworkInterface in _interfaces )
			{
				if (inet.active)
				{
					active.push(inet);
					//printInterface(inet);
				}
			}
			
			return active;
		}
		
		/**
		 * Get primary active interface address.
		 *  
		 * @return InterfaceAddress instance.
		 */		
		public function get activeAddress() : InterfaceAddress
		{
			var address:InterfaceAddress;
			
			if (activeInterfaces.length > 0 && activeInterfaces[0].addresses.length > 0)
			{
				log("Primary active interface:\n");
				
				printInterface(activeInterfaces[0]);

				address = activeInterfaces[0].addresses[0];
			}
			
			return address;
		}
		
		/**
		 * Constructor. 
		 */		
		public function NetworkInfoSupport()
		{
			super();
			
			_info = NetworkInfo.networkInfo;
			_info.addEventListener(Event.NETWORK_CHANGE, onNetworkChange);
			
			listInterfaces();
		}
		
		private function onNetworkChange( event:Event ) : void
		{
			log("One of the network interfaces has changed.\n");
			
			listInterfaces();
			
			dispatchEvent( new Event(event.type, true, true) );
		}
		
		private function listInterfaces() : void
		{
			_interfaces = _info.findInterfaces();
			
			log("Total network interfaces: " + _interfaces.length + "\n");
			
			/*for each ( var inet:NetworkInterface in _interfaces )
			{
				printInterface( inet );
			}*/
			
		}
		
		private function printInterface( inet:NetworkInterface ) : void
		{
			var msg:String = "-----------------------------------\n";
			msg += "Name: " + inet.name + "\n";
			msg += "Displayname: " + inet.displayName + "\n";
			msg += "Active: " + inet.active + "\n";
			msg += "Hardware Address: " + inet.hardwareAddress + "\n";
			msg += "MTU: " + inet.mtu + "\n";
			
			log( msg );
			
			if (inet.addresses.length > 0)
			{
				printAddresses( inet.addresses );
			}
		}

		private function printAddresses( addresses:Vector.<InterfaceAddress> ):void
		{
			var msg:String = "Addresses:\n";
			
			for each (var address:InterfaceAddress in addresses)
			{
				msg += " - " + address.ipVersion + " address: " + address.address + "\n";
				if (address.broadcast)
				{
					msg += " - Broadcast: " + address.broadcast + "\n";
				}
			}
			
			log( msg );
		}
		
		private function log( msg:String ):void
		{
			var log:LogEvent = new LogEvent(LogEvent.UPDATE, msg);
			dispatchEvent( log );
		}
		
	}
}