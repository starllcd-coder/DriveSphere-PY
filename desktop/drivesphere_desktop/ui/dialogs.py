from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


def show_modal_dialog(
    parent: QWidget | None,
    title: str,
    message: str,
    *,
    is_rtl: bool = False,
    confirm_label: str = "OK",
    cancel_label: str | None = None,
    confirm_object_name: str = "DsBtnPrimary",
    width: int = 520,
) -> bool:
    dialog = QDialog(parent)
    dialog.setObjectName("DsDialog")
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.resize(width, 180 if cancel_label else 160)
    dialog.setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)

    root = QVBoxLayout(dialog)
    root.setContentsMargins(18, 14, 18, 14)
    root.setSpacing(10)

    title_lbl = QLabel(title)
    title_lbl.setObjectName("DsDialogTitle")
    title_lbl.setAlignment(Qt.AlignRight if is_rtl else Qt.AlignLeft)

    body = QLabel(message or "")
    body.setObjectName("DsDialogBody")
    body.setWordWrap(True)
    body.setAlignment((Qt.AlignTop | Qt.AlignRight) if is_rtl else (Qt.AlignTop | Qt.AlignLeft))

    actions = QHBoxLayout()
    actions.setSpacing(8)
    actions.addStretch(1)

    cancel_btn = None
    if cancel_label:
        cancel_btn = QPushButton(cancel_label)
        cancel_btn.setObjectName("DsBtnGhost")
        cancel_btn.clicked.connect(dialog.reject)
        actions.addWidget(cancel_btn)

    confirm_btn = QPushButton(confirm_label)
    confirm_btn.setObjectName(confirm_object_name)
    confirm_btn.clicked.connect(dialog.accept)
    actions.addWidget(confirm_btn)

    root.addWidget(title_lbl)
    root.addWidget(body)
    root.addStretch(1)
    root.addLayout(actions)

    confirm_btn.setDefault(True)
    if cancel_btn:
        cancel_btn.setAutoDefault(False)
    return dialog.exec() == QDialog.Accepted


def show_info(
    parent: QWidget | None,
    *,
    is_rtl: bool,
    title_en: str,
    message_en: str,
    title_ar: str,
    message_ar: str,
) -> bool:
    return show_modal_dialog(
        parent,
        title_ar if is_rtl else title_en,
        message_ar if is_rtl else message_en,
        is_rtl=is_rtl,
        confirm_label="\u062d\u0633\u0646\u0627\u064b" if is_rtl else "OK",
        confirm_object_name="DsBtnPrimary",
    )


def show_warning(
    parent: QWidget | None,
    *,
    is_rtl: bool,
    title_en: str,
    message_en: str,
    title_ar: str,
    message_ar: str,
) -> bool:
    return show_modal_dialog(
        parent,
        title_ar if is_rtl else title_en,
        message_ar if is_rtl else message_en,
        is_rtl=is_rtl,
        confirm_label="\u062d\u0633\u0646\u0627\u064b" if is_rtl else "OK",
        confirm_object_name="DsBtnDanger",
    )


def ask_confirm(
    parent: QWidget | None,
    *,
    is_rtl: bool,
    title_en: str,
    message_en: str,
    title_ar: str,
    message_ar: str,
    danger: bool = True,
) -> bool:
    return show_modal_dialog(
        parent,
        title_ar if is_rtl else title_en,
        message_ar if is_rtl else message_en,
        is_rtl=is_rtl,
        confirm_label="\u062a\u0623\u0643\u064a\u062f" if is_rtl else "Confirm",
        cancel_label="\u0625\u0644\u063a\u0627\u0621" if is_rtl else "Cancel",
        confirm_object_name="DsBtnDanger" if danger else "DsBtnPrimary",
        width=560,
    )
