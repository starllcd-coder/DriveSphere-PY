from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.ui.pages.list_page import ActionSpec, ColumnSpec, FilterSpec, ListPage, OptionSpec
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QLineEdit, QVBoxLayout


class PaymentsPage(ListPage):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__(
			api_client=api_client,
			endpoint="/api/payments/",
			title_en="Payments",
			title_ar="المدفوعات",
			filters=[
				FilterSpec("booking_id", "Booking ID", "معرف الحجز"),
				FilterSpec("customer", "Customer Name", "اسم العميل"),
				FilterSpec(
					"method",
					"Method",
					"الطريقة",
					[
						OptionSpec("", "All Methods", "كل الطرق"),
						OptionSpec("CASH", "Cash", "نقداً"),
						OptionSpec("CARD", "Card", "بطاقة"),
						OptionSpec("BANK_TRANSFER", "Bank", "تحويل بنكي"),
					],
				),
			],
			columns=[
				ColumnSpec("Date", "التاريخ", "date"),
				ColumnSpec("Receipt", "الإيصال", "receipt_number"),
				ColumnSpec("Booking", "الحجز", "booking_id"),
				ColumnSpec("Customer", "العميل", "customer_name"),
				ColumnSpec("Method", "الطريقة", "method"),
				ColumnSpec("Amount", "المبلغ", "amount"),
				ColumnSpec("Status", "الحالة", "status"),
			],
		)
		self.set_actions(
			[
				ActionSpec("new", "New Payment", "مدفوعات جديدة", variant="primary", requires_selection=False),
				ActionSpec("refund", "Refund", "استرداد", variant="ghost", requires_selection=False),
				ActionSpec("edit", "Edit Payment", "تعديل المدفوعات", variant="ghost"),
				ActionSpec("delete", "Delete Payment", "حذف المدفوعات", variant="danger"),
				ActionSpec("export", "Export Payment Report", "تصدير تقرير المدفوعات", variant="export", requires_selection=False),
			]
		)

	def _payment_dialog(self, title_en: str, title_ar: str, include_id: bool = False) -> tuple[QDialog, dict[str, QLineEdit | QComboBox]]:
		dlg = QDialog(self)
		dlg.setWindowTitle(title_ar if self.is_rtl else title_en)
		layout = QVBoxLayout(dlg)
		form = QFormLayout()
		fields: dict[str, QLineEdit | QComboBox] = {}
		if include_id:
			payment_id = QLineEdit()
			fields["payment_id"] = payment_id
			form.addRow("Payment ID" if not self.is_rtl else "معرف الدفعة", payment_id)
		booking = QLineEdit()
		amount = QLineEdit()
		method = QComboBox()
		for value in ["CASH", "CARD", "BANK_TRANSFER"]:
			method.addItem(value, value)
		notes = QLineEdit()
		fields["booking_id"] = booking
		fields["amount"] = amount
		fields["method"] = method
		fields["notes"] = notes
		form.addRow("Booking ID" if not self.is_rtl else "معرف الحجز", booking)
		form.addRow("Amount" if not self.is_rtl else "المبلغ", amount)
		form.addRow("Method" if not self.is_rtl else "الطريقة", method)
		form.addRow("Notes" if not self.is_rtl else "ملاحظات", notes)
		layout.addLayout(form)
		buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
		buttons.accepted.connect(dlg.accept)

		initial = {
			k: (v.currentData() if isinstance(v, QComboBox) else v.text())
			for k, v in fields.items()
		}

		def reject_with_guard() -> None:
			current = {
				k: (v.currentData() if isinstance(v, QComboBox) else v.text())
				for k, v in fields.items()
			}
			if current != initial and not self.confirm_action(
				"Discard Changes",
				"Discard unsaved payment changes?",
				"تجاهل التغييرات",
				"هل تريد تجاهل تغييرات الدفع غير المحفوظة؟",
			):
				return
			dlg.reject()

		buttons.rejected.connect(reject_with_guard)
		layout.addWidget(buttons)
		return dlg, fields

	def action_new(self) -> None:
		dlg, fields = self._payment_dialog("New Payment", "مدفوعات جديدة")
		if dlg.exec() != QDialog.Accepted:
			return
		try:
			self.api_client.post_json(
				"/api/payments/create/",
				{
					"booking_id": fields["booking_id"].text().strip(),
					"amount": fields["amount"].text().strip(),
					"method": fields["method"].currentData(),
					"notes": fields["notes"].text().strip(),
				},
			)
			self.notify("Payment created", "تم إنشاء الدفعة")
			self.load_data()
		except Exception as exc:
			self.notify(f"Create failed: {exc}", f"فشل الإنشاء: {exc}")

	def action_refund(self) -> None:
		dlg, fields = self._payment_dialog("Refund", "استرداد", include_id=True)
		if self.selected_row:
			pid = self.selected_row.get("id")
			if pid is not None:
				fields["payment_id"].setText(str(pid))
		if dlg.exec() != QDialog.Accepted:
			return
		try:
			self.api_client.post_json(
				"/api/refunds/create/",
				{
					"payment_id": fields["payment_id"].text().strip(),
					"amount": fields["amount"].text().strip(),
					"method": fields["method"].currentData(),
					"notes": fields["notes"].text().strip(),
				},
			)
			self.notify("Refund created", "تم إنشاء الاسترداد")
			self.load_data()
		except Exception as exc:
			self.notify(f"Refund failed: {exc}", f"فشل الاسترداد: {exc}")

	def action_edit(self) -> None:
		if not self.require_selection():
			return
		pid = self.selected_id()
		dlg, fields = self._payment_dialog("Edit Payment", "تعديل المدفوعات")
		if self.selected_row:
			fields["booking_id"].setText(str(self.selected_row.get("booking_id", "")))
			fields["amount"].setText(str(self.selected_row.get("amount", "")))
			fields["notes"].setText(str(self.selected_row.get("notes", "")))
		if dlg.exec() != QDialog.Accepted:
			return
		try:
			self.api_client.post_json(
				f"/api/payments/{pid}/update/",
				{
					"amount": fields["amount"].text().strip(),
					"method": fields["method"].currentData(),
					"notes": fields["notes"].text().strip(),
				},
			)
			self.notify("Payment updated", "تم تحديث المدفوعات")
			self.load_data()
		except Exception as exc:
			self.notify(f"Update failed: {exc}", f"فشل التحديث: {exc}")

	def action_delete(self) -> None:
		if not self.require_selection():
			return
		if not self.confirm_action(
			"Void Payment",
			"Void selected payment?",
			"إلغاء الدفعة",
			"هل تريد إلغاء الدفعة المحددة؟",
		):
			return
		pid = self.selected_id()
		try:
			self.api_client.post_json(f"/api/payments/{pid}/void/", {})
			self.notify("Payment voided", "تم إلغاء المدفوعات")
			self.load_data()
		except Exception as exc:
			self.notify(f"Void failed: {exc}", f"فشل الإلغاء: {exc}")

	def action_export(self) -> None:
		path, _ = QFileDialog.getSaveFileName(
			self,
			"Save Payments Report" if not self.is_rtl else "حفظ تقرير المدفوعات",
			"payments_report.pdf",
			"PDF Files (*.pdf)",
		)
		if not path:
			return
		try:
			content = self.api_client.download_file("/api/payments/report.pdf")
			with open(path, "wb") as file_obj:
				file_obj.write(content)
			self.notify("Report exported", "تم تصدير التقرير")
		except Exception as exc:
			self.notify(f"Export failed: {exc}", f"فشل التصدير: {exc}")
