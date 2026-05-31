"""
Tests for YAML format compatibility.
"""

from click.testing import CliRunner

import hdem
from hdem import YAMLHandler, cli


def test_read_legacy_records_format(tmp_path, monkeypatch):
    """Legacy flat records files are accepted."""
    monkeypatch.setattr("hdem.ZONES_DIR", tmp_path)
    (tmp_path / "example.com.yaml").write_text(
        """
id: oldZoneId123456789012
name: example.com
records:
  - id: 0123456789abcdef0123456789abcdef
    type: A
    name: www
    value: 192.0.2.1
  - id: fedcba9876543210fedcba9876543210
    type: MX
    name: '@'
    value: 10 mail.example.com.
""".lstrip()
    )

    zone = YAMLHandler().read_zone("example.com")

    assert zone is not None
    assert zone.id == "oldZoneId123456789012"
    assert len(zone.records) == 2
    assert [(rrset.name, rrset.type) for rrset in zone.rrsets] == [("www", "A"), ("@", "MX")]


def test_read_rrset_format(tmp_path, monkeypatch):
    """Native RRSet files are accepted."""
    monkeypatch.setattr("hdem.ZONES_DIR", tmp_path)
    (tmp_path / "example.com.yaml").write_text(
        """
version: 2
id: 123456
name: example.com
ttl: 86400
rrsets:
  - name: '@'
    type: MX
    records:
      - value: 10 mail.example.com.
      - value: 20 backup.example.com.
  - name: txt
    type: TXT
    records:
      - value: '"hello"'
        comment: greeting
""".lstrip()
    )

    zone = YAMLHandler().read_zone("example.com")

    assert zone is not None
    assert zone.id == "123456"
    assert zone.ttl == 86400
    assert len(zone.records) == 3
    assert len(zone.rrsets) == 2
    assert zone.rrsets[1].records[0].comment == "greeting"


def test_write_preserves_legacy_format(tmp_path, monkeypatch):
    """Normal writes preserve legacy files."""
    monkeypatch.setattr("hdem.ZONES_DIR", tmp_path)
    (tmp_path / "example.com.yaml").write_text(
        """
id: oldZoneId123456789012
name: example.com
records:
  - id: 0123456789abcdef0123456789abcdef
    type: A
    name: www
    value: 192.0.2.1
""".lstrip()
    )

    handler = YAMLHandler()
    zone = handler.read_zone("example.com")
    assert zone is not None

    handler.write_zone(zone)

    written = (tmp_path / "example.com.yaml").read_text()
    assert "version: 2" not in written
    assert "rrsets:" not in written
    assert "records:" in written
    assert "0123456789abcdef0123456789abcdef" in written


def test_write_can_force_rrset_format(tmp_path, monkeypatch):
    """Explicit migration writes the v2 RRSet format."""
    monkeypatch.setattr("hdem.ZONES_DIR", tmp_path)
    (tmp_path / "example.com.yaml").write_text(
        """
id: oldZoneId123456789012
name: example.com
records:
  - id: 0123456789abcdef0123456789abcdef
    type: A
    name: www
    value: 192.0.2.1
""".lstrip()
    )

    handler = YAMLHandler()
    zone = handler.read_zone("example.com")
    assert zone is not None

    handler.write_zone(zone, file_format="rrsets")

    written = (tmp_path / "example.com.yaml").read_text()
    assert "version: 2" in written
    assert "rrsets:" in written
    assert "0123456789abcdef0123456789abcdef" not in written


def test_migrate_uses_zones_dir_option(tmp_path):
    """The CLI can operate on a non-default zones directory."""
    original_zones_dir = hdem.ZONES_DIR
    zones_dir = tmp_path / "inventory"
    zones_dir.mkdir()
    (zones_dir / "example.com.yaml").write_text(
        """
id: oldZoneId123456789012
name: example.com
records:
  - id: 0123456789abcdef0123456789abcdef
    type: A
    name: www
    value: 192.0.2.1
""".lstrip()
    )

    try:
        result = CliRunner().invoke(cli, ["--zones-dir", str(zones_dir), "migrate", "example.com"])
    finally:
        hdem.ZONES_DIR = original_zones_dir

    assert result.exit_code == 0
    written = (zones_dir / "example.com.yaml").read_text()
    assert "version: 2" in written
    assert "rrsets:" in written


def test_migrate_uses_zones_dir_env(tmp_path):
    """The CLI can read the zones directory from HDEM_ZONES_DIR."""
    original_zones_dir = hdem.ZONES_DIR
    zones_dir = tmp_path / "inventory"
    zones_dir.mkdir()
    (zones_dir / "example.com.yaml").write_text(
        """
id: oldZoneId123456789012
name: example.com
records:
  - id: 0123456789abcdef0123456789abcdef
    type: A
    name: www
    value: 192.0.2.1
""".lstrip()
    )

    try:
        result = CliRunner().invoke(cli, ["migrate", "example.com"], env={"HDEM_ZONES_DIR": str(zones_dir)})
    finally:
        hdem.ZONES_DIR = original_zones_dir

    assert result.exit_code == 0
    written = (zones_dir / "example.com.yaml").read_text()
    assert "version: 2" in written
    assert "rrsets:" in written


def test_write_creates_missing_zones_dir(tmp_path, monkeypatch):
    """Writing a zone creates the configured directory only when needed."""
    zones_dir = tmp_path / "missing"
    monkeypatch.setattr("hdem.ZONES_DIR", zones_dir)

    zone = YAMLHandler()._read_legacy_zone(
        {
            "id": "oldZoneId123456789012",
            "name": "example.com",
            "records": [{"id": "", "type": "A", "name": "www", "value": "192.0.2.1"}],
        }
    )

    YAMLHandler().write_zone(zone)

    assert (zones_dir / "example.com.yaml").exists()
