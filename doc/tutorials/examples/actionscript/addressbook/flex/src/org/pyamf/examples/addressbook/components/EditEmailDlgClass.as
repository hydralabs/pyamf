/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.addressbook.components
{
	import flash.events.MouseEvent;
	
	import mx.events.FlexEvent;
	import mx.managers.PopUpManager;
	
	import org.pyamf.examples.addressbook.models.Email;
	
	import spark.components.TextInput;
	import spark.components.TitleWindow;

	public class EditEmailDlgClass extends TitleWindow
	{
		[Bindable]
		public var email			: Email;
		
		public var emailLabel		: TextInput;
		public var emailText		: TextInput;
		
		/**
		 * Constructor. 
		 */		
		public function EditEmailDlgClass()
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
			email.label = emailLabel.text;
			email.email = emailText.text;
			PopUpManager.removePopUp(this);	
		}
		
	}
}