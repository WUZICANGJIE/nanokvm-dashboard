{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [ python313 uv ruff nodejs chromium ];
  shellHook = ''
    export UV_PYTHON=${pkgs.python313}/bin/python3
    export CHROMIUM_EXECUTABLE=${pkgs.chromium}/bin/chromium
    export PLAYWRIGHT_NODEJS_PATH=${pkgs.nodejs}/bin/node
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ]}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  '';
}
