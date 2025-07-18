from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import angr
import archinfo
import cle
from angr.angrdb import AngrDB
from PySide6.QtWidgets import QMessageBox

from angrmanagement.logic.threads import gui_thread_schedule
from angrmanagement.ui.dialogs import LoadBinary

from .job import InstanceJob

if TYPE_CHECKING:
    from angr.knowledge_base import KnowledgeBase

    from angrmanagement.data.instance import Instance
    from angrmanagement.logic.jobmanager import JobContext


_l = logging.getLogger(__name__)


class LoadBinaryJob(InstanceJob):
    """
    Job to display binary load dialog and create angr project.
    """

    def __init__(self, instance: Instance, fname, load_options=None, on_finish=None) -> None:
        super().__init__("Loading file", instance, on_finish=on_finish)
        self.load_options = load_options or {}
        self.fname = fname

    def run(self, ctx: JobContext) -> None:
        ctx.set_progress(5)

        load_as_blob = False

        partial_ld = None
        try:
            # Try automatic loading
            partial_ld = cle.Loader(
                self.fname,
                perform_relocations=False,
                load_debug_info=False,
                auto_load_libs=False,
                main_opts={"ignore_missing_arch": True},
            )
        except archinfo.arch.ArchNotFound:
            _l.warning("Could not identify binary architecture.")
            partial_ld = None
            load_as_blob = True
        except (cle.CLECompatibilityError, cle.CLEError):
            # Continue loading as blob
            _l.debug("Try loading the binary as a blob.")
            load_as_blob = True

        if partial_ld is None and load_as_blob:
            try:
                # Try loading as blob; dummy architecture (x86) required, user will select proper arch
                partial_ld = cle.Loader(self.fname, main_opts={"backend": "blob", "arch": "x86"})
            except cle.CLECompatibilityError:
                # Failed to load executable, even as blob!
                gui_thread_schedule(LoadBinary.binary_loading_failed, (self.fname,))
                return

        if partial_ld is None:
            _l.warning("Failed to load binary in Cle; partial_ld is None.")
            gui_thread_schedule(LoadBinary.binary_loading_failed, (self.fname,))
            return

        ctx.set_progress(50)
        new_load_options, simos = gui_thread_schedule(
            LoadBinary.run, (partial_ld, partial_ld.main_object.__class__, partial_ld.main_object.os)
        )
        if new_load_options is None:
            return

        engine = None
        if hasattr(new_load_options["arch"], "pcode_arch"):
            engine = angr.engines.UberEnginePcode

        self.load_options.update(new_load_options)

        proj = angr.Project(self.fname, load_options=self.load_options, engine=engine, simos=simos)
        ctx.set_progress(95)

        def callback() -> None:
            self.instance._reset_containers()
            self.instance.project.am_obj = proj
            self.instance.project.am_event()

        gui_thread_schedule(callback, ())


class LoadAngrDBJob(InstanceJob):
    """
    Load an angr database file and return a new angr project.
    """

    def __init__(
        self,
        instance: Instance,
        file_path: str,
        kb_names: list[str],
        other_kbs: dict[str, KnowledgeBase] | None = None,
        extra_info: dict | None = None,
        on_finish=None,
    ) -> None:
        super().__init__("Loading angr database", instance, on_finish=on_finish)
        self.file_path = file_path
        self.kb_names = kb_names
        self.other_kbs = other_kbs
        self.extra_info = extra_info
        self.blocking = True

        self.project = None

    def run(self, ctx: JobContext) -> None:
        ctx.set_progress(5)

        angrdb = AngrDB()
        try:
            proj = angrdb.load(
                self.file_path, kb_names=self.kb_names, other_kbs=self.other_kbs, extra_info=self.extra_info
            )
        except angr.errors.AngrIncompatibleDBError as ex:
            _l.critical("Failed to load the angr database because of compatibility issues.", exc_info=True)
            gui_thread_schedule(
                QMessageBox.critical,
                (None, "Error", f"Failed to load the angr database because of compatibility issues.\nDetails: {ex}"),
            )
            return
        except angr.errors.AngrDBError as ex:
            _l.critical("Failed to load the angr database because of compatibility issues.", exc_info=True)
            gui_thread_schedule(
                QMessageBox.critical, (None, "Error", f"Failed to load the angr database.\nDetails: {ex}")
            )
            _l.critical("Failed to load the angr database.", exc_info=True)
            return

        self.project = proj

        ctx.set_progress(100)
