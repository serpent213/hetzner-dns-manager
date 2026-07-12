# Release Process

## Version Update Locations

Keep the version in sync across **all** of these:

1. **pyproject.toml** - `version = "0.2.1"`
2. **hdem** - `VERSION = "0.2.1"` (printed by `hdem --version`)
3. **uv.lock** - the project's own `version` entry; run `uv lock` after
   editing `pyproject.toml` (a build also refreshes it)

## Release Steps

1. **Update version numbers** in `pyproject.toml` and `hdem`
2. **Sync the lockfile**:
   ```bash
   uv lock
   ```
3. **Update CHANGELOG.md** with new version and changes
4. **Build the package**:
   ```bash
   uv build
   ```
5. **Publish to PyPI**:
   ```bash
   # Set PyPI token (get from https://pypi.org/manage/account/token/)
   export UV_PUBLISH_TOKEN=pypi-...
   uv publish dist/hetzner_dns_manager-0.2.1*
   ```
6. **Create git tag**:
   ```bash
   git tag v0.2.X
   git push origin v0.2.X
   ```

## Notes

- The `hdem` script contains the version displayed by `--version` flag
- pyproject.toml version is used for package metadata and PyPI
- `pyproject.toml`, `hdem`, and `uv.lock` must all carry the same version
- Demo images in README.md reference specific version tags
