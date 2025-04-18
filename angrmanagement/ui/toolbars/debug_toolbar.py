from __future__ import annotations

from typing import TYPE_CHECKING, Any

import qtawesome as qta
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QComboBox, QLabel, QMenu

from angrmanagement.logic.debugger import Debugger, DebuggerListManager, DebuggerManager, DebuggerWatcher

from .toolbar import Toolbar, ToolbarAction, ToolbarSplitter

if TYPE_CHECKING:
    from angrmanagement.data.instance import Instance
    from angrmanagement.ui.main_window import MainWindow
    from angrmanagement.ui.workspace import Workspace


# pylint:disable=unused-argument,no-self-use
class AvailableDebuggersModel(QAbstractItemModel):
    """
    Data provider for available debuggers combo box.
    """

    def __init__(self, workspace: Workspace) -> None:
        super().__init__()
        self.debugger_mgr: DebuggerManager = workspace.main_instance.debugger_mgr
        self.debugger_list_mgr: DebuggerListManager = workspace.main_instance.debugger_list_mgr
        self.last_str = {}

    def rowCount(self, parent=None):  # pylint:disable=unused-argument
        return len(self.debugger_list_mgr.debugger_list) + 1

    def columnCount(self, parent=None) -> int:
        return 1

    def index(self, row, col, parent=None):
        return self.createIndex(row, col, None)

    def parent(self, index=None):  # type:ignore
        return QModelIndex()

    def data(self, index, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        row = index.row()
        dbg = self.index_to_debugger(row)
        self.last_str[row] = "No Debugger" if dbg is None else str(dbg)
        return self.last_str[row]

    def debugger_to_index(self, dbg: Debugger | None) -> int:
        return 0 if dbg is None else (self.debugger_list_mgr.debugger_list.index(dbg) + 1)

    def index_to_debugger(self, index: int) -> Debugger | None:
        return None if index == 0 else (self.debugger_list_mgr.debugger_list[index - 1])


class DebugToolbar(Toolbar):
    """
    Debugger Control Toolbar
    TODO: decouple this from MainWindow and workspace.instance (main_instance)
    """

    def __init__(self, main_window: MainWindow) -> None:
        super().__init__(main_window, "DebugToolbar")
        self.workspace: Workspace = main_window.workspace
        self.instance: Instance = self.workspace.main_instance

        self._cont_backward_act = ToolbarAction(
            qta.icon("fa5s.fast-backward"),
            "Continue-Backward",
            "Reverse-Continue",
            self._on_cont_backward,
        )
        self._step_backward_act = ToolbarAction(
            qta.icon("fa5s.step-backward"),
            "Step-Backward",
            "Reverse-Step",
            self._on_step_backward,
        )
        self._cont_act = ToolbarAction(qta.icon("fa5s.play"), "Continue", "Continue", self._on_cont)
        self._halt_act = ToolbarAction(qta.icon("fa5s.pause"), "Halt", "Halt", self._on_halt)
        self._step_act = ToolbarAction(qta.icon("fa5s.step-forward"), "Step", "Step", self._on_step)
        self._step_over_act = ToolbarAction(qta.icon("fa5s.share"), "Step Over", "Step Over", self._on_step_over)

        self._start_act = ToolbarAction(qta.icon("fa5s.running"), "Launch", "New Debugger", self._on_start)
        self._stop_act = ToolbarAction(qta.icon("fa5s.stop-circle"), "Stop", "Stop Debugging", self._on_stop)

        self.actions = [
            self._cont_backward_act,
            self._step_backward_act,
            self._cont_act,
            self._halt_act,
            self._step_act,
            self._step_over_act,
            ToolbarSplitter(),
            self._start_act,
            self._stop_act,
        ]
        self.qtoolbar()

        assert self._cached is not None
        self._cached.visibilityChanged.connect(self._on_visibility_changed)

        self._dbg_list_mgr = self.instance.debugger_list_mgr
        self._dbg_mgr = self.instance.debugger_mgr

        self._new_dbg_menu = QMenu(self._cached)

        self._new_dbg_sim = QAction("New simulation...", self._new_dbg_menu)
        self._new_dbg_sim.triggered.connect(self.workspace.main_window.open_newstate_dialog)
        self._new_dbg_menu.addAction(self._new_dbg_sim)

        self._new_dbg_trace = QAction("New trace debugger", self._new_dbg_menu)
        self._new_dbg_trace.triggered.connect(self.workspace.create_trace_debugger)
        self._new_dbg_menu.addAction(self._new_dbg_trace)

        self._new_dbg_menu.aboutToShow.connect(self._update_new_dbg_list)
        self._cached_actions[self._start_act].setMenu(self._new_dbg_menu)
        self._update_new_dbg_list()

        self._dbg_model = AvailableDebuggersModel(self.workspace)
        self._dbg_combo = QComboBox()
        self._dbg_combo.setMinimumWidth(250)
        self._dbg_combo.setModel(self._dbg_model)
        self._dbg_combo.activated.connect(self._select_dbg_by_index)
        self._cached.addWidget(self._dbg_combo)
        self._update_dbg_list_combo()

        self._run_lbl = QLabel()
        self._run_lbl.setText("")
        self._cached.addWidget(self._run_lbl)

        self._dbg_watcher: DebuggerWatcher | None = None

    def _on_visibility_changed(self, visible: bool) -> None:
        if visible:
            self.instance.debugger_list_mgr.debugger_list.am_subscribe(self._update_dbg_list_combo)
            self._dbg_watcher = DebuggerWatcher(self._dbg_state_changed, self._dbg_mgr.debugger)
            self._dbg_state_changed()
        else:
            assert self._dbg_watcher is not None
            self._dbg_watcher.shutdown()
            self._dbg_watcher = None

    def _select_dbg_by_index(self, index: int) -> None:
        dbg = self._dbg_model.index_to_debugger(index)
        self._dbg_mgr.set_debugger(dbg)

    def _dbg_state_changed(self) -> None:
        self._update_dbg_list_combo()
        self._update_state()

    def _select_current_dbg_in_combo(self, *args, **kwargs) -> None:  # pylint:disable=unused-argument
        dbg = self._dbg_mgr.debugger.am_obj
        self._dbg_combo.setCurrentIndex(self._dbg_model.debugger_to_index(dbg))

    def _update_new_dbg_list(self) -> None:
        self._new_dbg_sim.setDisabled(self.instance.project.am_none)
        self._new_dbg_trace.setDisabled(self.instance.current_trace.am_none)

    def _update_dbg_list_combo(self, *args, **kwargs) -> None:  # pylint:disable=unused-argument
        dl = self.instance.debugger_list_mgr.debugger_list
        self._dbg_combo.setEnabled(len(dl) > 0)
        self._select_current_dbg_in_combo()
        self._dbg_model.layoutChanged.emit()
        self._dbg_combo.update()

    def _update_state(self) -> None:
        dbg = self._dbg_mgr.debugger.am_obj
        dbg_active = dbg is not None

        def q(a):
            return self._cached_actions[a]

        q(self._step_act).setEnabled(dbg_active and dbg.can_step_forward)
        q(self._step_over_act).setEnabled(dbg_active and dbg.can_step_forward)
        q(self._step_backward_act).setEnabled(dbg_active and dbg.can_step_backward)
        q(self._cont_backward_act).setEnabled(dbg_active and dbg.can_continue_backward)
        q(self._cont_act).setEnabled(dbg_active and dbg.can_continue_forward)
        q(self._cont_act).setVisible(not (dbg_active and dbg.can_halt))
        q(self._halt_act).setEnabled(dbg_active and dbg.can_halt)
        q(self._halt_act).setVisible(dbg_active and dbg.can_halt)
        q(self._start_act).setEnabled(True)
        q(self._stop_act).setEnabled(dbg_active and dbg.can_stop)

        if dbg_active:
            self._run_lbl.setText(dbg.state_description)
        else:
            self._run_lbl.setText("")

    def _on_start(self) -> None:
        assert self._cached is not None
        self._cached.widgetForAction(self._cached_actions[self._start_act]).showMenu()

    def _on_stop(self) -> None:
        self._dbg_mgr.debugger.stop()
        self._dbg_list_mgr.remove_debugger(self._dbg_mgr.debugger.am_obj)

    def _on_cont(self) -> None:
        self._dbg_mgr.debugger.continue_forward()

    def _on_cont_backward(self) -> None:
        self._dbg_mgr.debugger.continue_backward()

    def _on_halt(self) -> None:
        self._dbg_mgr.debugger.halt()

    def _on_step(self) -> None:
        self._dbg_mgr.debugger.step_forward()

    def _on_step_over(self) -> None:
        b = self._dbg_mgr.debugger.simstate.block()
        until_addr = b.instruction_addrs[0] + b.size if b.instructions == 1 and b.vex.jumpkind == "Ijk_Call" else None
        self._dbg_mgr.debugger.step_forward(until_addr=until_addr)

    def _on_step_backward(self) -> None:
        self._dbg_mgr.debugger.step_backward()
