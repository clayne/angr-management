from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from angrmanagement.data.breakpoint import Breakpoint, BreakpointType
from angrmanagement.ui.widgets import QAddressInput

if TYPE_CHECKING:
    from angrmanagement.ui.workspace import Workspace


class BreakpointDialog(QDialog):
    """
    Dialog to edit breakpoints.
    TODO: decouple breakpoints from workspace.instance (main_instance)
    """

    def __init__(self, breakpoint_: Breakpoint, workspace: Workspace, parent=None) -> None:
        super().__init__(parent)
        self.breakpoint = breakpoint_
        self.workspace = workspace
        self.setWindowTitle("Edit Breakpoint")
        self.main_layout: QVBoxLayout = QVBoxLayout()
        self._type_radio_group: QButtonGroup | None = None
        self._address_box: QAddressInput | None = None
        self._size_box: QLineEdit | None = None
        self._comment_box: QLineEdit | None = None
        self._status_label: QLabel | None = None
        self._ok_button: QPushButton | None = None
        self._init_widgets()
        self.setLayout(self.main_layout)
        self._validate()

    #
    # Private methods
    #

    def _init_widgets(self) -> None:
        layout = QGridLayout()
        self.main_layout.addLayout(layout)
        self._status_label = QLabel(self)

        row = 0
        layout.addWidget(QLabel("Break on:", self), row, 0, Qt.AlignmentFlag.AlignRight)
        self._type_radio_group = QButtonGroup(self)
        self._type_radio_group.addButton(QRadioButton("Execute", self), BreakpointType.Execute.value)
        self._type_radio_group.addButton(QRadioButton("Write", self), BreakpointType.Write.value)
        self._type_radio_group.addButton(QRadioButton("Read", self), BreakpointType.Read.value)
        for b in self._type_radio_group.buttons():
            layout.addWidget(b, row, 1)
            row += 1

        self._type_radio_group.button(self.breakpoint.type.value).setChecked(True)

        layout.addWidget(QLabel("Address:", self), row, 0, Qt.AlignmentFlag.AlignRight)
        self._address_box = QAddressInput(
            self._on_address_changed, self.workspace, parent=self, default=f"{self.breakpoint.addr:#x}"
        )
        layout.addWidget(self._address_box, row, 1)
        row += 1

        layout.addWidget(QLabel("Size:", self), row, 0, Qt.AlignmentFlag.AlignRight)
        self._size_box = QLineEdit(self)
        self._size_box.setText(f"{self.breakpoint.size:#x}")
        self._size_box.textChanged.connect(self._on_size_changed)
        layout.addWidget(self._size_box, row, 1)
        row += 1

        layout.addWidget(QLabel("Comment:", self), row, 0, Qt.AlignmentFlag.AlignRight)
        self._comment_box = QLineEdit(self)
        self._comment_box.setText(self.breakpoint.comment)
        layout.addWidget(self._comment_box, row, 1)
        row += 1

        self.main_layout.addWidget(self._status_label)

        buttons = QDialogButtonBox(parent=self)
        buttons.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._on_ok_clicked)
        buttons.rejected.connect(self.close)
        self._ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setEnabled(False)
        self.main_layout.addWidget(buttons)

    def _set_valid(self, valid: bool) -> None:
        if not valid:
            self._status_label.setText("Invalid")
            self._status_label.setProperty("class", "status_invalid")
        else:
            self._status_label.setText("Valid")
            self._status_label.setProperty("class", "status_valid")

        self._ok_button.setEnabled(valid)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

    def _get_size(self):
        try:
            return int(self._size_box.text(), 0)
        except ValueError:
            pass
        return None

    #
    # Event handlers
    #

    def _validate(self) -> None:
        self._set_valid(bool(self._address_box.target is not None and self._get_size()))

    def _on_address_changed(self, new_text) -> None:  # pylint: disable=unused-argument
        self._validate()

    def _on_size_changed(self, new_text) -> None:  # pylint: disable=unused-argument
        self._validate()

    def _on_ok_clicked(self) -> None:
        self.breakpoint.type = BreakpointType(self._type_radio_group.checkedId())
        self.breakpoint.addr = self._address_box.target
        self.breakpoint.size = self._get_size()
        self.breakpoint.comment = self._comment_box.text()
        self.workspace.main_instance.breakpoint_mgr.breakpoints.am_event()
        self.accept()
