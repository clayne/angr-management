from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from angrmanagement.data.object_container import EventSentinel


def _make_config_entry_value(init_value, type_):
    class ConfigurationEntryValue(QObject, EventSentinel):
        """
        An object container that both calls am_event() and emits 'changed' on an update
        This object allows usage of both types of event triggers
        """

        changed = Signal(type_)

        def __init__(self, value) -> None:
            QObject.__init__(self)
            if not hasattr(self, "am_subscribers"):
                EventSentinel.__init__(self)
            self._value = value

        def get(self):
            return self._value

        def set(self, value) -> None:
            """
            Set the value, if it changes, trigger events
            """
            if value != self._value:
                self._value = value
                self.am_event()
                self.changed.emit(value)

    return ConfigurationEntryValue(init_value)


class ConfigurationEntry:
    """
    Describes a configuration entry in angr management.
    """

    __slots__ = ("name", "type_", "_value", "default_value")

    def __init__(self, name: str, type_, value, default_value=None) -> None:
        self.name = name
        self.type_ = type_
        self._value = _make_config_entry_value(value, self.type_)
        self.default_value = value if default_value is None and value is not None else default_value

    def copy(self):
        """
        Copies over data, does *not* copy subscribers, signal connections, or slot connections
        """
        return ConfigurationEntry(self.name, self.type_, self.value, default_value=self.default_value)

    @property
    def value(self):
        return self._value.get()

    @value.setter
    def value(self, new) -> None:
        self._value.set(new)

    #
    # Event functions
    #

    @property
    def changed(self) -> Signal:
        return self._value.changed

    def subscribe(self, listener) -> None:
        self._value.am_subscribe(listener)

    def unsubscribe(self, listener) -> None:
        self._value.am_unsubscribe(listener)
