# Changelog

## v0.3.0 – 2026-05-31

### Added

- Manage Hetzner Cloud DNS zones through the official `hcloud-python` client and `HCLOUD_TOKEN`.
- Add native RRSet YAML support while keeping legacy flat `records:` files readable.
- Add `hdem migrate [DOMAIN]` and `hdem migrate --all` for explicit v2 YAML migration.
- Add `--zones-dir` and `HDEM_ZONES_DIR` for selecting the local zone inventory directory.

### Changed

- Preserve the source YAML format on normal writes; only `migrate` rewrites legacy files to RRSet format.
- Apply updates and deletes through Cloud DNS RRSet operations instead of old per-record bulk endpoints.
- Update documentation and dependency metadata for the Hetzner Cloud DNS API.
- Create the local zones directory only when writing zone files.

### Removed

- Remove use of the retired `dns.hetzner.com` DNS API and `HETZNER_DNS_API_TOKEN`.

## v0.2.1 – 2025-05-09

### Improved

- Little README touch up
- About 50% test coverage

## v0.2.0 – 2025-05-09

### Added

- Display record's TTL values from DNS in output table

### Fixed

- TXT record validation and concatenation for escaped quotes

### Improved

- Resolve authoritative NS only once per zone - reduces wall time for "check" to < 50%

## v0.1.0 – 2025-05-08

- Initial release
