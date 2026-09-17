{
  description = "NixOS support for the CHUWI MiniBook X";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      lib.mkPackages =
        {
          pkgs,
          linuxPackages ? pkgs.linuxPackages,
        }:
        import ./nix/packages.nix {
          inherit linuxPackages pkgs;
          source = self;
        };

      lib.mkVbtFirmware =
        {
          pkgs,
          sourceVbt,
          refreshRate ? null,
          rotation ? null,
          linuxPackages ? pkgs.linuxPackages,
        }:
        let
          packages = self.lib.mkPackages {
            inherit linuxPackages pkgs;
          };
        in
        import ./nix/vbt-firmware.nix {
          inherit
            pkgs
            refreshRate
            rotation
            sourceVbt
            ;
          vbtPatch = packages.vbtPatch;
        };

      nixosModules.default = import ./nix/module.nix { inherit self; };
      nixosModules.chuwi-minibook = self.nixosModules.default;

      overlays.default = final: _prev: {
        chuwi-minibook = self.lib.mkPackages { pkgs = final; };
      };

      packages.${system} = self.lib.mkPackages { inherit pkgs; };
    };
}
