from __future__ import annotations

import unittest

from common import AngrManagementTestCase, ProjectOpenTestCase

from angrmanagement.ui.views import (
    BreakpointsView,
    CallExplorerView,
    CodeView,
    ConsoleView,
    DataDepView,
    DependencyView,
    DisassemblyView,
    FunctionsView,
    HexView,
    JobsView,
    LogView,
    PatchesView,
    ProximityView,
    RegistersView,
    StackView,
    StringsView,
    SymexecView,
    TraceMapView,
    TracesView,
    TypesView,
)


class TestViewsOpen(AngrManagementTestCase):
    """Tests that all views open, without first opening a project."""

    def test_breakpoints_view(self):
        self.main.workspace.show_view("breakpoints", BreakpointsView)

    def test_call_explorer_view(self):
        self.main.workspace.show_view("call_explorer", CallExplorerView)

    def test_code_view(self):
        self.main.workspace.show_view("code", CodeView)

    def test_console_view(self):
        self.main.workspace.show_view("console", ConsoleView)

    def test_data_dep_view(self):
        self.main.workspace.show_view("data_dep", DataDepView)

    def test_dependency_view(self):
        self.main.workspace.show_view("dependency", DependencyView)

    def test_disassembly_view(self):
        self.main.workspace.show_view("disassembly", DisassemblyView)

    def test_functions_view(self):
        self.main.workspace.show_view("functions", FunctionsView)

    def test_hex_view(self):
        self.main.workspace.show_view("hex", HexView)

    def test_jobs_view(self):
        self.main.workspace.show_view("jobs", JobsView)

    def test_log_view(self):
        self.main.workspace.show_view("log", LogView)

    def test_patches_view(self):
        self.main.workspace.show_view("patches", PatchesView)

    def test_proximity_view(self):
        self.main.workspace.show_view("proximity", ProximityView)

    def test_registers_view(self):
        self.main.workspace.show_view("registers", RegistersView)

    def test_stack_view(self):
        self.main.workspace.show_view("stack", StackView)

    def test_strings_view(self):
        self.main.workspace.show_view("strings", StringsView)

    def test_symexec_view(self):
        self.main.workspace.show_view("symexec", SymexecView)

    def test_trace_map_view(self):
        self.main.workspace.show_view("trace_map", TraceMapView)

    def test_traces_view(self):
        self.main.workspace.show_view("traces", TracesView)

    def test_types_view(self):
        self.main.workspace.show_view("types", TypesView)


class TestViewsOpenWithProject(ProjectOpenTestCase, TestViewsOpen):
    """Tests that all views open, after opening a project."""


if __name__ == "__main__":
    unittest.main()
