/**
 * Copyright (c) The PyAMF Project.
 * See LICENSE.txt for details.
*/
package org.pyamf.examples.addressbook.components
{
	import flash.display.DisplayObject;
	import flash.events.MouseEvent;
	
	import mx.controls.DataGrid;
	import mx.core.FlexGlobals;
	import mx.events.FlexEvent;
	import mx.managers.PopUpManager;
	import mx.rpc.AbstractOperation;
	import mx.rpc.events.ResultEvent;
	import mx.rpc.remoting.mxml.RemoteObject;
	
	import org.pyamf.examples.addressbook.models.Email;
	import org.pyamf.examples.addressbook.models.PhoneNumber;
	import org.pyamf.examples.addressbook.models.User;
	
	import spark.components.TextInput;
	import spark.components.TitleWindow;

	public class EditUserDlgClass extends TitleWindow
	{
		[Bindable]
		public var user				: User;
		
		public var emails			: DataGrid;
		public var phone_numbers	: DataGrid;
		public var firstName		: TextInput;
		public var lastName			: TextInput;
		
		/**
		 * Constructor. 
		 */		
		public function EditUserDlgClass()
		{
			super();
			
			addEventListener(FlexEvent.CREATION_COMPLETE, creationCompleteHandler);
		}
		
		protected function creationCompleteHandler( event:FlexEvent ):void
		{
			PopUpManager.centerPopUp(this);
			
			if (user.isAttrLazy("emails"))
			{
				user.loadAttr("emails");
			}
			
			if (user.isAttrLazy("phone_numbers"))
			{
				user.loadAttr("phone_numbers");
			}
		}
		
		override protected function closeButton_clickHandler(event:MouseEvent):void
		{
			close();
		}
		
		protected function close():void
		{
			PopUpManager.removePopUp(this);	
		}
		
		/**
		 * Add a new e-mail address.
		 */
		protected function addEmail():void
		{
			var email:Email = new Email();
			user.emails.addItem(email);
			var editEmailDlg:EditEmailDlg = new EditEmailDlg();
			editEmailDlg.email = email;
			PopUpManager.addPopUp(editEmailDlg, DisplayObject(FlexGlobals.topLevelApplication));	
		}
		
		/**
		 * Edit an existing e-mail address.
		 */
		protected function editEmail():void
		{
			var editEmailDlg:EditEmailDlg = new EditEmailDlg();
			editEmailDlg.email = Email(emails.selectedItem);
			PopUpManager.addPopUp(editEmailDlg, DisplayObject(FlexGlobals.topLevelApplication));	
		}
		
		/**
		 * Remove e-mail addresses
		 */
		protected function removeEmails():void
		{
			for each (var item:Object in emails.selectedItems)
			{
				var i:int = user.emails.getItemIndex(item);
				user.emails.removeItemAt(i);
			}
		}
		
		/**
		 * Add a new phone number.
		 */
		protected function addPhone():void
		{
			var phone_number:PhoneNumber = new PhoneNumber();
			user.phone_numbers.addItem(phone_number);
			
			var editPhoneDlg:EditPhoneDlg = new EditPhoneDlg();
			editPhoneDlg.phone = phone_number;
			
			PopUpManager.addPopUp(editPhoneDlg, DisplayObject(FlexGlobals.topLevelApplication));	
		}
		
		/**
		 * Edit an existing e-mail address.
		 */
		protected function editPhone():void
		{
			var editPhoneDlg:EditPhoneDlg = new EditPhoneDlg();
			editPhoneDlg.phone = PhoneNumber(phone_numbers.selectedItem);
			
			PopUpManager.addPopUp(editPhoneDlg, DisplayObject(FlexGlobals.topLevelApplication));	
		}
		
		/**
		 * Remove e-mail addresses.
		 */
		protected function removePhones():void
		{
			for each (var item:Object in phone_numbers.selectedItems)
			{
				var i:int = user.phone_numbers.getItemIndex(item);
				user.phone_numbers.removeItemAt(i);
			}
		}
		
		/**
		 * Persist a user.
		 */
		protected function save():void
		{
			user.first_name = firstName.text;
			user.last_name = lastName.text;
			
			var remoteObj:RemoteObject = FlexGlobals.topLevelApplication.getService();
			var operation:AbstractOperation = remoteObj.getOperation('save');
            operation.addEventListener(ResultEvent.RESULT, save_resultHandler);
            operation.send(user);
		}
		
		protected function save_resultHandler(event:Event):void
		{
			event.target.removeEventListener(ResultEvent.RESULT, save_resultHandler);
			if (!user.isPersistent())
			{
				FlexGlobals.topLevelApplication.loadUsers();
			}
			
			close();
		}
		
	}
}
