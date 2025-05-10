{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: {
  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    version = lib.removeSuffix "\n" (builtins.readFile ./.python-version);
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  # See full reference at https://devenv.sh/reference/options/
}
