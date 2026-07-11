from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable
from urllib.parse import urlencode

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from drivesphere_desktop.core.api_client import ApiClient
from drivesphere_desktop.ui.dialogs import ask_confirm, show_info


@dataclass(frozen=True)
class OptionSpec:
    value: str
    label_en: str
    label_ar: str


@dataclass(frozen=True)
class FilterSpec:
    key: str
    placeholder_en: str
    placeholder_ar: str
    options: list[OptionSpec] | None = None


@dataclass(frozen=True)
class ColumnSpec:
    label_en: str
    label_ar: str
    path: str


@dataclass(frozen=True)
class ActionSpec:
    key: str
    label_en: str
    label_ar: str
    variant: str = "ghost"
    requires_selection: bool = True


class ListPage(QWidget):
    def __init__(
        self,
        api_client: ApiClient,
        endpoint: str,
        title_en: str,
        title_ar: str,
        filters: list[FilterSpec],
        columns: list[ColumnSpec],
    ) -> None:
        super().__init__()
        self.api_client = api_client
        self.endpoint = endpoint
        self.title_en = title_en
        self.title_ar = title_ar
        self.filters = filters
        self.columns = columns
        self.filter_widgets: dict[str, QWidget] = {}
        self.filter_specs: dict[str, FilterSpec] = {}
        self.action_specs: list[ActionSpec] = []
        self.action_buttons: dict[str, QPushButton] = {}
        self.rows_cache: list[dict] = []
        self.selected_row: dict | None = None
        self.is_rtl = False
        self._status_columns = [idx for idx, col in enumerate(columns) if "status" in col.path.lower()]
        self._numeric_columns = [
            idx
            for idx, col in enumerate(columns)
            if any(key in col.path.lower() for key in ("amount", "rate", "cost", "total"))
        ]
        self._date_columns = [
            idx
            for idx, col in enumerate(columns)
            if any(key in col.path.lower() for key in ("date", "due", "pickup", "return"))
        ]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        self.filters_card = QFrame()
        self.filters_card.setObjectName("ListFiltersCard")
        filters_layout = QHBoxLayout(self.filters_card)
        filters_layout.setContentsMargins(12, 12, 12, 12)
        filters_layout.setSpacing(10)

        for spec in filters:
            self.filter_specs[spec.key] = spec
            if spec.options:
                box = QComboBox()
                box.setObjectName("ListFilterSelect")
                for option in spec.options:
                    box.addItem(option.label_en, option.value)
                box.currentIndexChanged.connect(self.load_data)
                self.filter_widgets[spec.key] = box
                filters_layout.addWidget(box)
            else:
                edit = QLineEdit()
                edit.setObjectName("ListFilterInput")
                edit.setPlaceholderText(spec.placeholder_en)
                edit.textChanged.connect(self.load_data)
                self.filter_widgets[spec.key] = edit
                filters_layout.addWidget(edit)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("LangToggleButton")
        self.refresh_btn.clicked.connect(self.load_data)
        filters_layout.addWidget(self.refresh_btn)
        root.addWidget(self.filters_card)

        table_card = QFrame()
        table_card.setObjectName("ListTableCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 12, 12, 12)

        self.table_title = QLabel(title_en)
        self.table_title.setObjectName("AuthLabel")
        table_layout.addWidget(self.table_title)

        self.table = QTableWidget(0, len(columns))
        self.table.setObjectName("ListTable")
        self.table.setHorizontalHeaderLabels([c.label_en for c in columns])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        table_layout.addWidget(self.table)

        self.status = QLabel("")
        self.status.setObjectName("AuthLabel")
        self.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        table_layout.addWidget(self.status)

        root.addWidget(table_card, 1)

        self.actions_card = QFrame()
        self.actions_card.setObjectName("ListActionsBar")
        self.actions_layout = QHBoxLayout(self.actions_card)
        self.actions_layout.setContentsMargins(12, 10, 12, 10)
        self.actions_layout.setSpacing(8)
        self.actions_card.hide()
        root.addWidget(self.actions_card)

        self._apply_column_widths()

    def set_actions(self, actions: list[ActionSpec]) -> None:
        self.action_specs = actions
        self.action_buttons.clear()
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if not actions:
            self.actions_card.hide()
            return
        for action in actions:
            prefix = self._action_prefix(action.variant)
            btn = QPushButton(f"{prefix}{action.label_en}")
            btn.setObjectName(f"DsBtn{action.variant.capitalize()}")
            btn.clicked.connect(lambda checked=False, k=action.key: self._on_action_clicked(k))
            self.actions_layout.addWidget(btn)
            self.action_buttons[action.key] = btn
        self.actions_layout.addStretch(1)
        self.actions_card.show()
        self._refresh_action_states()

    def _on_action_clicked(self, key: str) -> None:
        handler = getattr(self, f"action_{key}", None)
        if callable(handler):
            handler()
            return
        show_info(
            self,
            is_rtl=self.is_rtl,
            title_en="Action",
            message_en="Feature will be implemented in next step.",
            title_ar="إجراء",
            message_ar="سيتم تنفيذ هذه الميزة في الخطوة التالية.",
        )

    def selected_id(self) -> str:
        if not self.selected_row:
            return ""
        value = self.selected_row.get("id")
        return "" if value is None else str(value)

    def notify(self, message_en: str, message_ar: str | None = None) -> None:
        self.status.setText(message_ar if self.is_rtl and message_ar else message_en)

    def require_selection(self) -> bool:
        if self.selected_row is not None:
            return True
        self.notify("Select a row first", "اختر صفا أولا")
        return False

    def confirm_action(self, title_en: str, message_en: str, title_ar: str, message_ar: str) -> bool:
        return ask_confirm(
            self,
            is_rtl=self.is_rtl,
            title_en=title_en,
            message_en=message_en,
            title_ar=title_ar,
            message_ar=message_ar,
            danger=True,
        )

    def _action_prefix(self, variant: str) -> str:
        if variant == "primary":
            return "+ "
        if variant == "danger":
            return "! "
        if variant == "export":
            return "> "
        return ""

    def _refresh_action_states(self) -> None:
        has_row = self.selected_row is not None
        for action in self.action_specs:
            btn = self.action_buttons.get(action.key)
            if not btn:
                continue
            btn.setEnabled((not action.requires_selection) or has_row)

    def _apply_column_widths(self) -> None:
        for idx in range(len(self.columns)):
            if idx in self._status_columns:
                self.table.setColumnWidth(idx, 130)
            elif idx in self._numeric_columns:
                self.table.setColumnWidth(idx, 120)
            elif idx in self._date_columns:
                self.table.setColumnWidth(idx, 130)

    def set_language(self, lang: str) -> None:
        self.is_rtl = lang == "ar"
        self.table_title.setText(self.title_ar if self.is_rtl else self.title_en)
        self.refresh_btn.setText("تحديث" if self.is_rtl else "Refresh")

        headers = [c.label_ar if self.is_rtl else c.label_en for c in self.columns]
        self.table.setHorizontalHeaderLabels(headers)

        for key, widget in self.filter_widgets.items():
            spec = self.filter_specs[key]
            if isinstance(widget, QLineEdit):
                widget.setPlaceholderText(spec.placeholder_ar if self.is_rtl else spec.placeholder_en)
                widget.setAlignment(Qt.AlignRight if self.is_rtl else Qt.AlignLeft)
            elif isinstance(widget, QComboBox):
                current = widget.currentData()
                widget.blockSignals(True)
                widget.clear()
                for option in spec.options or []:
                    widget.addItem(option.label_ar if self.is_rtl else option.label_en, option.value)
                index = widget.findData(current)
                widget.setCurrentIndex(max(index, 0))
                widget.blockSignals(False)

        for action in self.action_specs:
            btn = self.action_buttons.get(action.key)
            if btn:
                prefix = self._action_prefix(action.variant)
                text = action.label_ar if self.is_rtl else action.label_en
                btn.setText(f"{prefix}{text}")

    def _params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        for key, widget in self.filter_widgets.items():
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QComboBox):
                value = str(widget.currentData() or "")
            else:
                value = ""
            if value:
                params[key] = value
        return params

    def _extract(self, item: dict, path: str) -> str:
        value = item
        for part in path.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                value = None
            if value is None:
                break
        if value is None:
            return "-"
        return str(value)

    def _set_rows(self, rows: Iterable[dict]) -> None:
        rows_list = list(rows)
        self.rows_cache = rows_list
        self.selected_row = None
        self.table.setRowCount(len(rows_list))
        for row_idx, item in enumerate(rows_list):
            for col_idx, spec in enumerate(self.columns):
                value = self._extract(item, spec.path)
                if col_idx in self._status_columns:
                    badge = QLabel(value)
                    badge.setObjectName("ListStatusBadge")
                    badge.setProperty("status", value.upper())
                    badge.setAlignment(Qt.AlignCenter)
                    self.table.setCellWidget(row_idx, col_idx, badge)
                    continue
                if col_idx in self._date_columns and value not in ("-", ""):
                    value = value.split("T", 1)[0]
                if col_idx in self._numeric_columns and value not in ("-", ""):
                    try:
                        value = f"{Decimal(value):,.3f}"
                    except (InvalidOperation, ValueError):
                        pass
                cell = QTableWidgetItem(value)
                if col_idx in self._numeric_columns:
                    align = Qt.AlignLeft if self.is_rtl else Qt.AlignRight
                    cell.setTextAlignment(align | Qt.AlignVCenter)
                elif self.is_rtl:
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, cell)
        self._refresh_action_states()

    def _on_selection_changed(self) -> None:
        index = self.table.currentRow()
        if index < 0 or index >= len(self.rows_cache):
            self.selected_row = None
        else:
            self.selected_row = self.rows_cache[index]
        self._refresh_action_states()

    def load_data(self) -> None:
        try:
            params = self._params()
            qs = urlencode(params)
            url = self.endpoint if not qs else f"{self.endpoint}?{qs}"
            data = self.api_client.get_json(url)
            if data.get("ok") is False:
                raise RuntimeError(data.get("error", "Request failed"))
            rows = data.get("results", [])
            self._set_rows(rows)
            if self.api_client.is_online:
                self.status.setText(f"{len(rows)} عنصر" if self.is_rtl else f"{len(rows)} items")
            else:
                self.status.setText(
                    f"{len(rows)} عنصر (مخزن محلي)"
                    if self.is_rtl
                    else f"{len(rows)} items (cached offline)"
                )
        except Exception as exc:
            self.table.setRowCount(0)
            self.status.setText(f"فشل التحميل: {exc}" if self.is_rtl else f"Load failed: {exc}")
