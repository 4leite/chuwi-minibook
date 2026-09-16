{
  pkgs,
  refreshRate,
  rotation,
  sourceVbt,
  vbtPatch,
}:
pkgs.stdenvNoCC.mkDerivation {
  pname = "chuwi-minibook-vbt";
  version = "${toString refreshRate}hz-rotation${toString rotation}";
  dontUnpack = true;
  nativeBuildInputs = [ vbtPatch ];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/lib/firmware
    vbt_patch \
      ${sourceVbt} \
      --hz ${toString refreshRate} \
      --rotation ${toString rotation} \
      $out/lib/firmware/vbt
    runHook postInstall
  '';

  meta = {
    description = "Configured CHUWI MiniBook VBT firmware";
    platforms = pkgs.lib.platforms.linux;
  };
}
