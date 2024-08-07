from __future__ import annotations

import binascii
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QContextMenuEvent, QCursor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QMenu, QMessageBox, QTableWidget, QTableWidgetItem

if TYPE_CHECKING:
    from angr.knowledge_plugins.patches import Patch
    from PySide6.QtGui import QCloseEvent

    from angrmanagement.data.instance import Instance


class QPatchTableItem:
    """
    Item in the patch table describing a patch.
    """

    def __init__(self, patch, old_bytes) -> None:
        self.patch = patch
        self.old_bytes = old_bytes

    def widgets(self):
        patch = self.patch

        widgets = [
            QTableWidgetItem(f"{patch.addr:x}"),
            QTableWidgetItem(f"{len(patch)} bytes"),
            QTableWidgetItem(binascii.hexlify(self.old_bytes).decode("ascii") if self.old_bytes else "<unknown>"),
            QTableWidgetItem(binascii.hexlify(patch.new_bytes).decode("ascii")),
            QTableWidgetItem(patch.comment or ""),
        ]

        for w in widgets[:-1]:
            w.setFlags(w.flags() & ~Qt.ItemIsEditable)

        return widgets


class QPatchTable(QTableWidget):
    """
    Table of all patches.
    """

    HEADER = ["Address", "Size", "Old Bytes", "New Bytes", "Comment"]

    def __init__(self, instance: Instance, parent) -> None:
        super().__init__(parent)

        self.setColumnCount(len(self.HEADER))
        self.setHorizontalHeaderLabels(self.HEADER)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

        self.items = []
        self.instance = instance
        self.instance.patches.am_subscribe(self._watch_patches)
        self._reloading: bool = False
        self.cellChanged.connect(self._on_cell_changed)
        self.reload()

    def _on_cell_changed(self, row: int, column: int) -> None:
        """
        Handle item change events, specifically to support editing comments.
        """
        if not self._reloading and column == 4:
            comment_text = self.item(row, column).text()
            self.items[row].patch.comment = comment_text
            self.instance.patches.am_event()

    def current_patch(self):
        selected_index = self.currentRow()
        if 0 <= selected_index < len(self.items):
            return self.items[selected_index]
        else:
            return None

    def reload(self) -> None:
        self._reloading = True
        self.clearContents()

        self.items = (
            [
                QPatchTableItem(item, self._get_bytes(self.instance.project, item.addr, len(item)))
                for item in self.instance.project.kb.patches.values()
            ]
            if not self.instance.project.am_none
            else []
        )
        items_count = len(self.items)
        self.setRowCount(items_count)

        for idx, item in enumerate(self.items):
            for i, it in enumerate(item.widgets()):
                self.setItem(idx, i, it)

        self._reloading = False

    def _watch_patches(self, **kwargs) -> None:  # pylint: disable=unused-argument
        if not self.instance.patches.am_none:
            self.reload()

    @staticmethod
    def _get_bytes(proj, addr: int, size: int):
        try:
            return proj.loader.memory.load(addr, size)
        except KeyError:
            return None

    def get_selected_patches(self) -> set[Patch]:
        """
        Get the set of selected patches.
        """
        return {self.items[idx.row()].patch for idx in self.selectedIndexes()}

    def revert_selected_patches(self) -> None:
        """
        Revert any selected patches.
        """
        dlg = QMessageBox()
        dlg.setWindowTitle("Revert patches")
        dlg.setText("Are you sure you want to revert selected patches?")
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if dlg.exec_() != QMessageBox.StandardButton.Yes:
            return

        selected_patches = self.get_selected_patches()
        if selected_patches:
            for patch in selected_patches:
                self.instance.patches.remove_patch(patch.addr)
            self.instance.patches.am_event(removed=selected_patches)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # pylint: disable=unused-argument
        """
        Display view context menu.
        """
        mnu = QMenu(self)
        selected_patches = self.get_selected_patches()
        if len(selected_patches) > 0:
            act = QAction("Revert selected patches", mnu)
            act.triggered.connect(self.revert_selected_patches)
            mnu.addAction(act)
        mnu.exec_(QCursor.pos())

    def closeEvent(self, event: QCloseEvent) -> None:  # pylint:disable=unused-argument
        self.instance.patches.am_unsubscribe(self._watch_patches)
