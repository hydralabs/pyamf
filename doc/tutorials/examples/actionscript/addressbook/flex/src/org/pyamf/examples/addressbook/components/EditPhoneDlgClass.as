/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.addressbook.components
{
	import flash.events.MouseEvent;
	
	import mx.events.FlexEvent;
	import mx.managers.PopUpManager;
	
	import org.pyamf.examples.addressbook.models.PhoneNumber;
	
	import spark.components.TextInput;
	import spark.components.TitleWindow;

	public class EditPhoneDlgClass extends TitleWindow
	{
		[Bindable]
		public var phone			: PhoneNumber;
			
		public var phoneLabel		: TextInput;
		public var phoneNumber		: TextInput;
		
		/**
		 * Constructor. 
		 */		
		public function EditPhoneDlgClass()
		{
			super();
			
			addEventListener(FlexEvent.CREATION_COMPLETE, creationCompleteHandler);
		}
		
		protected function creationCompleteHandler( event:FlexEvent ):void
		{
			PopUpManager.centerPopUp(this);
		}
		
		override protected function closeButton_clickHandler(event:MouseEvent):void
		{
			close();
		}
		
		protected function close():void
		{
			phone.label = phoneLabel.text;
			phone.number = phoneNumber.text;
			PopUpManager.removePopUp(this);	
		}
			
	}
}