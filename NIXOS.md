# NixOS

The flake provides a NixOS module and packages for the MiniBook fixes in this
repository. Add it as an input:

```nix
inputs.chuwi-minibook.url = "github:4leite/chuwi-minibook/chewbacca";
```

Import the module:

```nix
{
  imports = [ inputs.chuwi-minibook.nixosModules.default ];
}
```

Capture the original VBT from the running machine before enabling the complete
default configuration:

```sh
sudo nix run github:4leite/chuwi-minibook/chewbacca#captureVbt -- \
  /path/to/your/config/firmware/source-vbt.bin
```

The command refuses to replace an existing capture. Add the captured file to
the host configuration, then configure its path:

```nix
hardware.chuwi-minibook.vbt.source = ./firmware/source-vbt.bin;
```

The module enables the tested MiniBook X N150 configuration by default:

- all four kernel-module fixes
- patched Goodix firmware
- patched SensorProxy using the display accelerometer
- patched thermald
- VBT generated from the captured original at 90 Hz with panel rotation 1
- disabled panel self refresh
- patched Mutter tablet-to-laptop transform handling
- repository diagnostic and VBT tools

Every part can be changed independently under `hardware.chuwi-minibook`.
For example:

```nix
hardware.chuwi-minibook = {
  goodix.enable = false;
  thermald.enable = false;
  vbt.enable = false;
  mutter.enable = false;

  sensorProxy = {
    orientationSensor = "base";
    panelOrientation = "auto";
  };
};
```

The VBT settings are declarative:

```nix
hardware.chuwi-minibook.vbt = {
  source = ./firmware/source-vbt.bin;
  refreshRate = 90;
  rotation = 1;
};
```

Nix builds `vbt_patch`, generates the firmware, and reuses the cached result
until the source VBT, settings, or patcher changes.

The available component switches are:

```text
goodix.enable
minibookEc.enable
dptfEnabler.enable
i2cDesignwareSpklen.enable
sensorProxy.enable
sensorProxy.setConvertibleChassis
thermald.enable
vbt.enable
vbt.source
vbt.refreshRate
vbt.rotation
vbt.installPatcher
tools.enable
disablePanelSelfRefresh
mutter.enable
```

The DPTF module's optional participants are controlled by
`dptfEnabler.enableFans` and `dptfEnabler.enableSensors`. Both default to
`false`, matching the upstream module defaults.
