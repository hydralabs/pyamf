/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.geoip.vo
{
	/**
	 * Geo info.
	 * 
	 * @since 0.1
	 */
	[RemoteClass(alias="org.pyamf.examples.geoip.GeoInfo")]
	public class GeoInfo
	{
		public var ip	   : String;
		public var country : Object;
		
		/**
		 * @param ip		IP address
		 * @param country	Object containing a name and code property (strings)
		 */		
		public function GeoInfo()
		{
			this.ip = ip;
			this.country = country;
		}

	}
}