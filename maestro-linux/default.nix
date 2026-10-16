# Users of NixOS or Nix can install this software by running:
#   nix-env -i -f .
{
  pkgs ? import <nixpkgs> { },
}:
let
  # Copy the current directory into the Nix store. Exclude nix-build's
  # result links so repeated builds do not incorporate previous outputs.
  appDir = builtins.path {
    path = ./.;
    name = "maestro-linux-260810";
    filter =
      path: type:
      let
        name = builtins.baseNameOf path;
      in
      name != ".git"
      && name != "result"
      && builtins.match "result-.*" name == null;
  };

  runtimeLibs = [
    pkgs.gtk2
    pkgs.libusb1
    pkgs.libgdiplus
  ];
  libraryPath = pkgs.lib.makeLibraryPath runtimeLibs;
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "maestro-linux";
  version = "260810";

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  dontUnpack = true;

  installPhase = ''
    runHook preInstall

    mkdir -p "$out/bin"

    makeWrapper "${pkgs.mono}/bin/mono" "$out/bin/UscCmd" \
      --add-flags "${appDir}/UscCmd" \
      --set LD_LIBRARY_PATH "${libraryPath}" \
      --set XMODIFIERS @im=none

    makeWrapper "${pkgs.mono}/bin/mono" "$out/bin/MaestroControlCenter" \
      --add-flags "${appDir}/MaestroControlCenter" \
      --set LD_LIBRARY_PATH "${libraryPath}" \
      --set XMODIFIERS @im=none

    runHook postInstall
  '';
}
