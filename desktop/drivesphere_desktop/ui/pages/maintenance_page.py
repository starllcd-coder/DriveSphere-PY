from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.ui.pages.list_page import ActionSpec, ColumnSpec, FilterSpec, ListPage, OptionSpec
from PySide6.QtWidgets import QFileDialog


class MaintenancePage(ListPage):
	def __init__(self, api_client: ApiClient) -> None:
		super().__init__(
			api_client=api_client,
			endpoint="/api/maintenance/",
			title_en="Maintenance",
			title_ar="الصيانة",
			filters=[
				FilterSpec("vehicle", "Vehicle / Brand / Model", "مركبة / ماركة / طراز"),
				FilterSpec("plate", "Plate", "اللوحة"),
				FilterSpec(
					"type",
					"Type",
					"النوع",
					[
						OptionSpec("", "All Types", "كل الأنواع"),
						OptionSpec("Service", "Service", "صيانة"),
						OptionSpec("Repair", "Repair", "إصلاح"),
						OptionSpec("Inspection", "Inspection", "تفتيش"),
					],
				),
				FilterSpec(
					"priority",
					"Priority",
					"الأولوية",
					[
						OptionSpec("", "Any Priority", "كل الأولويات"),
						OptionSpec("Low", "Low", "منخفض"),
						OptionSpec("Medium", "Medium", "متوسط"),
						OptionSpec("High", "High", "عالي"),
					],
				),
			],
			columns=[
				ColumnSpec("Date", "التاريخ", "date"),
				ColumnSpec("Vehicle", "المركبة", "vehicle"),
				ColumnSpec("Plate", "اللوحة", "plate"),
				ColumnSpec("Type", "النوع", "type"),
				ColumnSpec("Priority", "الأولوية", "priority"),
				ColumnSpec("Assignee", "المكلف", "assignee"),
				ColumnSpec("Due", "الموعد", "due"),
				ColumnSpec("Est Cost", "التكلفة المقدرة", "est_cost"),
				ColumnSpec("Notes", "ملاحظات", "notes"),
			],
		)
		self.set_actions(
			[
				ActionSpec("mark_done", "Mark Done", "وضع كمكتملة", variant="ghost"),
				ActionSpec("delete", "Delete Task", "حذف المهمة", variant="danger"),
				ActionSpec("export", "Export Maintenance Report", "تصدير تقرير الصيانة", variant="export", requires_selection=False),
			]
		)

	def action_mark_done(self) -> None:
		if not self.selected_row:
			return
		if not self.confirm_action(
			"Mark Done",
			"Mark selected task as done?",
			"وضع كمكتملة",
			"هل تريد وضع المهمة المحددة كمكتملة؟",
		):
			return
		task_id = self.selected_row.get("id")
		if not task_id:
			return
		try:
			self.api_client.post_json(f"/api/maintenance/{task_id}/done/", {})
			self.load_data()
		except Exception as exc:
			self.status.setText(f"فشل التنفيذ: {exc}" if self.is_rtl else f"Action failed: {exc}")

	def action_delete(self) -> None:
		if not self.selected_row:
			return
		if not self.confirm_action(
			"Delete Task",
			"Delete selected maintenance task?",
			"حذف المهمة",
			"هل تريد حذف مهمة الصيانة المحددة؟",
		):
			return
		task_id = self.selected_row.get("id")
		if not task_id:
			return
		try:
			self.api_client.post_json(f"/api/maintenance/{task_id}/delete/", {})
			self.load_data()
		except Exception as exc:
			self.status.setText(f"فشل التنفيذ: {exc}" if self.is_rtl else f"Action failed: {exc}")

	def action_export(self) -> None:
		path, _ = QFileDialog.getSaveFileName(
			self,
			"Save Maintenance Report" if not self.is_rtl else "حفظ تقرير الصيانة",
			"maintenance_report.pdf",
			"PDF Files (*.pdf)",
		)
		if not path:
			return
		try:
			content = self.api_client.download_file("/api/maintenance/report.pdf")
			with open(path, "wb") as file_obj:
				file_obj.write(content)
			self.notify("Report exported", "تم تصدير التقرير")
		except Exception as exc:
			self.notify(f"Export failed: {exc}", f"فشل التصدير: {exc}")
