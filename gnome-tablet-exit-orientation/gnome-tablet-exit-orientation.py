#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Restore GNOME's built-in display to logical normal after tablet mode."""

import argparse
import sys

from gi.repository import Gio, GLib

DISPLAY_NAME = "org.gnome.Mutter.DisplayConfig"
DISPLAY_PATH = "/org/gnome/Mutter/DisplayConfig"
NORMAL_TRANSFORM = 0
TEMPORARY_CONFIG = 1
RESTORE_DELAY_MS = 250
MAX_RESTORE_ATTEMPTS = 3


def create_display_proxy():
    return Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SESSION,
        Gio.DBusProxyFlags.NONE,
        None,
        DISPLAY_NAME,
        DISPLAY_PATH,
        DISPLAY_NAME,
        None,
    )


def build_logical_monitor_config(monitors, logical_monitors):
    monitor_details = {}
    builtin_connectors = set()

    for spec, modes, properties in monitors:
        connector = spec[0]
        current_mode = next(
            (mode[0] for mode in modes if mode[6].get("is-current", False)),
            None,
        )
        if current_mode is not None:
            monitor_details[connector] = current_mode
        if properties.get("is-builtin", False):
            builtin_connectors.add(connector)

    if not builtin_connectors:
        raise RuntimeError("Mutter did not report a built-in display")

    updated = []
    changed = False
    active_builtin = False

    for x, y, scale, old_transform, primary, monitor_specs, _properties in logical_monitors:
        connectors = []
        logical_is_builtin = False

        for spec in monitor_specs:
            connector = spec[0]
            if connector not in monitor_details:
                raise RuntimeError(
                    f"Mutter did not report a current mode for {connector}"
                )
            connectors.append((connector, monitor_details[connector], {}))
            logical_is_builtin = logical_is_builtin or connector in builtin_connectors

        transform = old_transform
        if logical_is_builtin:
            active_builtin = True
            transform = NORMAL_TRANSFORM
            changed = changed or old_transform != NORMAL_TRANSFORM

        updated.append((x, y, scale, transform, primary, connectors))

    if not active_builtin:
        raise RuntimeError("Mutter's built-in display is not active")

    return updated, changed


def restore_logical_normal(display):
    serial, monitors, logical_monitors, _properties = display.call_sync(
        "GetCurrentState",
        None,
        Gio.DBusCallFlags.NONE,
        -1,
        None,
    ).unpack()

    updated, changed = build_logical_monitor_config(monitors, logical_monitors)
    if not changed:
        return False

    parameters = GLib.Variant(
        "(uua(iiduba(ssa{sv}))a{sv})",
        (serial, TEMPORARY_CONFIG, updated, {}),
    )
    display.call_sync(
        "ApplyMonitorsConfig",
        parameters,
        Gio.DBusCallFlags.NONE,
        -1,
        None,
    )
    return True


class TabletExitOrientation:
    def __init__(self):
        self.display = create_display_proxy()
        managed = self.display.get_cached_property("PanelOrientationManaged")
        if managed is None:
            raise RuntimeError(
                "Mutter does not expose the PanelOrientationManaged property"
            )

        self.was_managed = managed.get_boolean()
        self.restore_source_id = 0
        self.restore_attempt = 0
        self.display.connect("g-properties-changed", self.properties_changed)

    def properties_changed(self, _proxy, changed, invalidated):
        managed = changed.lookup_value("PanelOrientationManaged", None)
        if managed is None and "PanelOrientationManaged" in invalidated:
            managed = self.display.get_cached_property("PanelOrientationManaged")
        if managed is None:
            return

        is_managed = managed.get_boolean()
        if is_managed:
            if self.restore_source_id:
                GLib.source_remove(self.restore_source_id)
                self.restore_source_id = 0
                self.restore_attempt = 0
        elif self.was_managed:
            self.schedule_restore(RESTORE_DELAY_MS)
        self.was_managed = is_managed

    def schedule_restore(self, delay_ms):
        if self.restore_source_id:
            GLib.source_remove(self.restore_source_id)
        self.restore_source_id = GLib.timeout_add(delay_ms, self.restore_after_exit)

    def restore_after_exit(self):
        self.restore_source_id = 0
        try:
            changed = restore_logical_normal(self.display)
        except (GLib.Error, RuntimeError) as error:
            self.restore_attempt += 1
            if self.restore_attempt < MAX_RESTORE_ATTEMPTS:
                print(
                    f"Failed to restore orientation; retrying: {error}",
                    file=sys.stderr,
                )
                self.schedule_restore(RESTORE_DELAY_MS)
            else:
                print(
                    f"Failed to restore orientation after "
                    f"{MAX_RESTORE_ATTEMPTS} attempts: {error}",
                    file=sys.stderr,
                )
                self.restore_attempt = 0
            return GLib.SOURCE_REMOVE

        self.restore_attempt = 0
        if changed:
            print("Restored built-in display to logical transform 0")
        return GLib.SOURCE_REMOVE


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply-once",
        action="store_true",
        help="restore logical transform 0 immediately and exit",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.apply_once:
        restore_logical_normal(create_display_proxy())
        return

    handler = TabletExitOrientation()
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
