#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("gnome-tablet-exit-orientation.py")
SPEC = importlib.util.spec_from_file_location("tablet_exit_orientation", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def monitor(connector, mode, builtin):
    spec = (connector, "vendor", "product", "serial")
    modes = [
        (
            mode,
            1920,
            1200,
            60.0,
            1.0,
            [1.0],
            {"is-current": True, "is-preferred": True},
        )
    ]
    return spec, modes, {"is-builtin": builtin}


def logical_monitor(connector, transform, primary):
    spec = (connector, "vendor", "product", "serial")
    return (0, 0, 1.0, transform, primary, [spec], {})


class ChangedProperties:
    def __init__(self, managed):
        self.managed = managed

    def lookup_value(self, name, _expected_type):
        if name == "PanelOrientationManaged":
            return MODULE.GLib.Variant("b", self.managed)
        return None


class BuildLogicalMonitorConfigTests(unittest.TestCase):
    def test_restores_only_builtin_monitor(self):
        monitors = [
            monitor("DSI-1", "1920x1200@60", True),
            monitor("HDMI-1", "2560x1440@60", False),
        ]
        logical_monitors = [
            logical_monitor("DSI-1", 1, True),
            logical_monitor("HDMI-1", 2, False),
        ]

        updated, changed = MODULE.build_logical_monitor_config(
            monitors, logical_monitors
        )

        self.assertTrue(changed)
        self.assertEqual(updated[0][3], 0)
        self.assertEqual(updated[1][3], 2)

    def test_does_not_reapply_normal_transform(self):
        monitors = [monitor("DSI-1", "1920x1200@60", True)]
        logical_monitors = [logical_monitor("DSI-1", 0, True)]

        updated, changed = MODULE.build_logical_monitor_config(
            monitors, logical_monitors
        )

        self.assertFalse(changed)
        self.assertEqual(updated[0][3], 0)

    def test_requires_active_builtin_monitor(self):
        monitors = [
            monitor("DSI-1", "1920x1200@60", True),
            monitor("HDMI-1", "2560x1440@60", False),
        ]
        logical_monitors = [logical_monitor("HDMI-1", 0, True)]

        with self.assertRaisesRegex(RuntimeError, "not active"):
            MODULE.build_logical_monitor_config(monitors, logical_monitors)

    def test_requires_current_mode(self):
        spec, modes, properties = monitor("DSI-1", "1920x1200@60", True)
        modes[0][6]["is-current"] = False

        with self.assertRaisesRegex(RuntimeError, "current mode"):
            MODULE.build_logical_monitor_config(
                [(spec, modes, properties)],
                [logical_monitor("DSI-1", 1, True)],
            )


class TabletExitOrientationTests(unittest.TestCase):
    def handler(self, was_managed):
        handler = object.__new__(MODULE.TabletExitOrientation)
        handler.display = None
        handler.was_managed = was_managed
        handler.restore_source_id = 0
        handler.restore_attempt = 0
        handler.scheduled = []
        handler.schedule_restore = handler.scheduled.append
        return handler

    def test_schedules_restore_on_managed_to_unmanaged_transition(self):
        handler = self.handler(was_managed=True)

        handler.properties_changed(None, ChangedProperties(False), [])

        self.assertEqual(handler.scheduled, [MODULE.RESTORE_DELAY_MS])

    def test_does_not_restore_for_repeated_managed_notification(self):
        handler = self.handler(was_managed=True)

        handler.properties_changed(None, ChangedProperties(True), [])

        self.assertEqual(handler.scheduled, [])


if __name__ == "__main__":
    unittest.main()
