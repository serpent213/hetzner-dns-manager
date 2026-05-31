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

  env.UV_NO_MANAGED_PYTHON = "false";

  # See full reference at https://devenv.sh/reference/options/
}
