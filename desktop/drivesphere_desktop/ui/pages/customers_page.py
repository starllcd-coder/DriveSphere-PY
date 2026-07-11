from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.ui.pages.list_page import ActionSpec, ColumnSpec, FilterSpec, ListPage
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
	QDialog,
	QDialogButtonBox,
	QFileDialog,
	QFormLayout,
	QHBoxLayout,
	QLineEdit,
	QListWidget,
	QPushButton,
	QVBoxLayout,
)


class CustomersPage(ListPage):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__(
			api_client=api_client,
			endpoint="/api/customers/",
			title_en="Customers",
			title_ar="العملاء",
			filters=[
				FilterSpec("name", "Customer Name", "اسم العميل"),
				FilterSpec("phone", "Phone", "الهاتف"),
				FilterSpec("id_number", "ID Number", "رقم الهوية"),
			],
			columns=[
				ColumnSpec("Name", "الاسم", "name"),
				ColumnSpec("Phone", "الهاتف", "phone_number"),
				ColumnSpec("ID Number", "رقم الهوية", "id_number"),
				ColumnSpec("Address", "العنوان", "address"),
			],
		)
		self.set_actions(
			[
				ActionSpec("upload_docs", "Upload ID/License", "رفع الهوية/الرخصة", variant="primary"),
				ActionSpec("view_docs", "View ID/License", "عرض الهوية/الرخصة", variant="ghost"),
				ActionSpec("edit", "Edit Customer", "تعديل العميل", variant="ghost"),
				ActionSpec("delete", "Delete Customer", "حذف العميل", variant="danger"),
			]
		)

	def action_edit(self) -> None:
		if not self.require_selection():
			return
		cid = self.selected_id()
		try:
			payload = self.api_client.get_json(f"/api/customers/{cid}/")
			customer = payload.get("customer", {})
		except Exception as exc:
			self.notify(f"Load failed: {exc}", f"فشل التحميل: {exc}")
			return

		dlg = QDialog(self)
		dlg.setWindowTitle("Edit Customer" if not self.is_rtl else "تعديل العميل")
		layout = QVBoxLayout(dlg)
		form = QFormLayout()
		name = QLineEdit(str(customer.get("name", "")))
		phone = QLineEdit(str(customer.get("phone_number", "")))
		id_number = QLineEdit(str(customer.get("id_number", "")))
		address = QLineEdit(str(customer.get("address", "")))
		form.addRow("Name" if not self.is_rtl else "الاسم", name)
		form.addRow("Phone" if not self.is_rtl else "الهاتف", phone)
		form.addRow("ID Number" if not self.is_rtl else "رقم الهوية", id_number)
		form.addRow("Address" if not self.is_rtl else "العنوان", address)
		layout.addLayout(form)
		buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
		buttons.accepted.connect(dlg.accept)
		initial = (name.text(), phone.text(), id_number.text(), address.text())

		def reject_with_guard() -> None:
			current = (name.text(), phone.text(), id_number.text(), address.text())
			if current != initial and not self.confirm_action(
				"Discard Changes",
				"Discard unsaved customer changes?",
				"تجاهل التغييرات",
				"هل تريد تجاهل تغييرات العميل غير المحفوظة؟",
			):
				return
			dlg.reject()

		buttons.rejected.connect(reject_with_guard)
		layout.addWidget(buttons)
		if dlg.exec() != QDialog.Accepted:
			return

		try:
			self.api_client.post_json(
				f"/api/customers/{cid}/update/",
				{
					"name": name.text().strip(),
					"phone_number": phone.text().strip(),
					"id_number": id_number.text().strip(),
					"address": address.text().strip(),
				},
			)
			self.notify("Customer updated", "تم تحديث العميل")
			self.load_data()
		except Exception as exc:
			self.notify(f"Update failed: {exc}", f"فشل التحديث: {exc}")

	def action_delete(self) -> None:
		if not self.require_selection():
			return
		if not self.confirm_action(
			"Delete Customer",
			"Delete selected customer?",
			"حذف العميل",
			"هل تريد حذف العميل المحدد؟",
		):
			return
		cid = self.selected_id()
		try:
			self.api_client.post_json(f"/api/customers/{cid}/delete/", {})
			self.notify("Customer deleted", "تم حذف العميل")
			self.load_data()
		except Exception as exc:
			self.notify(f"Delete failed: {exc}", f"فشل الحذف: {exc}")

	def action_view_docs(self) -> None:
		if not self.require_selection():
			return
		cid = self.selected_id()
		dlg = QDialog(self)
		dlg.setWindowTitle("Customer Documents" if not self.is_rtl else "مستندات العميل")
		dlg.resize(520, 420)
		layout = QVBoxLayout(dlg)
		lst = QListWidget()
		layout.addWidget(lst)
		controls = QHBoxLayout()
		open_page_btn = QPushButton("Open Page" if not self.is_rtl else "فتح الصفحة")
		controls.addWidget(open_page_btn)
		controls.addStretch(1)
		layout.addLayout(controls)
		try:
			payload = self.api_client.get_json(f"/api/customers/{cid}/docs/")
			for doc in payload.get("results", []):
				lst.addItem(f"{doc.get('doc_type_label', '')} | {doc.get('expiry_date', '')}")
			if lst.count() == 0:
				lst.addItem("No documents" if not self.is_rtl else "لا توجد مستندات")
		except Exception as exc:
			lst.addItem(f"Failed: {exc}")
		buttons = QDialogButtonBox(QDialogButtonBox.Close)
		buttons.rejected.connect(dlg.reject)
		layout.addWidget(buttons)

		open_page_btn.clicked.connect(
			lambda: QDesktopServices.openUrl(QUrl(self.api_client.absolute_url(f"/customers/{cid}/documents/")))
		)
		dlg.exec()

	def action_upload_docs(self) -> None:
		if not self.require_selection():
			return
		cid = self.selected_id()
		path, _ = QFileDialog.getOpenFileName(
			self,
			"Choose Document" if not self.is_rtl else "اختر مستند",
			"",
			"All Files (*.*)",
		)
		if not path:
			return
		try:
			with open(path, "rb") as file_obj:
				data = file_obj.read()
			self.api_client.post_form(
				f"/api/customers/{cid}/docs/upload/",
				{"doc_type": "OTHER", "notes": "Uploaded from desktop"},
				files={"file": (path.split("/")[-1].split("\\")[-1], data, "application/octet-stream")},
			)
			self.notify("Document uploaded", "تم رفع المستند")
		except Exception as exc:
			self.notify(f"Upload failed: {exc}", f"فشل الرفع: {exc}")
