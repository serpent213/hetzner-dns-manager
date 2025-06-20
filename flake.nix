{
  description = "Hetzner DNS Zone Manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
    ...
  }: let
    inherit (nixpkgs) lib;

    # Load a uv workspace from a workspace root.
    workspace = uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};

    # Create package overlay from workspace.
    overlay = workspace.mkPyprojectOverlay {
      # Prefer prebuilt binary wheels as a package source.
      sourcePreference = "wheel";
    };

    # Extend generated overlay with build fixups
    pyprojectOverrides = final: prev: {
      # Fix ruamel-yaml-clib missing setuptools
      ruamel-yaml-clib = prev.ruamel-yaml-clib.overrideAttrs (old: {
        nativeBuildInputs = old.nativeBuildInputs ++ [final.setuptools];
      });

      # Custom build fixups for hetzner-dns-manager
      hetzner-dns-manager = prev.hetzner-dns-manager.overrideAttrs (old: {
        # Handle the build hook requirement
        nativeBuildInputs = old.nativeBuildInputs ++ [final.hatchling];
      });
    };

    # Use x86_64-linux and aarch64-darwin
    forAllSystems = lib.genAttrs [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];
  in {
    # Package a virtual environment as our main application.
    packages = forAllSystems (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;

        # Construct package set
        pythonSet =
          (pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              pyprojectOverrides
            ]
          );
      in {
        default = pythonSet.mkVirtualEnv "hdem-env" workspace.deps.default;
        hdem = pythonSet.mkVirtualEnv "hdem-env" workspace.deps.default;
      }
    );

    # Make hdem runnable with `nix run`
    apps = forAllSystems (system: {
      default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/hdem";
      };
      hdem = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/hdem";
      };
    });

    # Development shells
    devShells = forAllSystems (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;
      in {
        default = pkgs.mkShell {
          packages = [
            python
            pkgs.uv
          ];
          env =
            {
              UV_PYTHON_DOWNLOADS = "never";
              UV_PYTHON = python.interpreter;
            }
            // lib.optionalAttrs pkgs.stdenv.isLinux {
              LD_LIBRARY_PATH = lib.makeLibraryPath pkgs.pythonManylinuxPackages.manylinux1;
            };
          shellHook = "unset PYTHONPATH";
        };
      }
    );
  };
}
