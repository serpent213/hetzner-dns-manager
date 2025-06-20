# Release Process

## Version Update Locations

Update version numbers in these files:

1. **pyproject.toml** - `version = "0.2.1"`
2. **hdem** - `VERSION = "0.2.0"`

## Release Steps

1. **Update version numbers** in both files above
2. **Update CHANGELOG.md** with new version and changes
3. **Build the package**:
   ```bash
   uv build
   ```
4. **Publish to PyPI**:
   ```bash
   # Set PyPI token (get from https://pypi.org/manage/account/token/)
   export UV_PUBLISH_TOKEN=pypi-...
   uv publish
   ```
5. **Create git tag**:
   ```bash
   git tag v0.2.X
   git push origin v0.2.X
   ```

## Notes

- The `hdem` script contains the version displayed by `--version` flag
- pyproject.toml version is used for package metadata and PyPI
- Both should be kept in sync
- Demo images in README.md reference specific version tags