/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.addressbook.models
{
	[Bindable]
	public class Email extends SAObject
	{
		public static var ALIAS	:String = 'org.pyamf.examples.addressbook.models.Email';
		
		public var id			: Object;
		public var user_id		: Object;
		public var label		: String;
		public var email		: String;
	}
}