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

Importing the module enables the tested MiniBook X N150 configuration by
default:

- all four kernel-module fixes
- patched Goodix firmware
- patched SensorProxy using the display accelerometer
- patched thermald
- 90 Hz VBT with panel rotation 1
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
vbt.installPatcher
tools.enable
disablePanelSelfRefresh
mutter.enable
```

The DPTF module's optional participants are controlled by
`dptfEnabler.enableFans` and `dptfEnabler.enableSensors`. Both default to
`false`, matching the upstream module defaults.
