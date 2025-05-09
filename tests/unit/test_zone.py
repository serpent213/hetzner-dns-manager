"""
Tests for the Zone dataclass.
"""

import pytest

from hdem import Zone, Record


class TestZoneValidation:
    """Test the validation of Zone dataclass."""

    def test_valid_zone_id(self):
        """Test that valid zone IDs are accepted."""
        # Valid 21-character alphanumeric string
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k", name="example.com")
        assert zone.id == "a1b2c3d4e5f6g7h8i9j0k"

        # Valid 22-character alphanumeric string
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com")
        assert zone.id == "a1b2c3d4e5f6g7h8i9j0k1"

    def test_invalid_zone_id(self):
        """Test that invalid zone IDs are rejected."""
        # Non-string ID
        with pytest.raises(ValueError, match="Zone ID must be a string"):
            Zone(id=123, name="example.com")  # type: ignore

        # Empty ID
        with pytest.raises(ValueError, match="Zone ID cannot be empty"):
            Zone(id="", name="example.com")

        # ID with invalid characters
        with pytest.raises(ValueError, match="Zone ID .* must be a 22-character alphanumeric string"):
            Zone(id="a1b2c3d4e5f6g7h8i9j0k1!", name="example.com")

        # ID too short
        with pytest.raises(ValueError, match="Zone ID .* must be a 22-character alphanumeric string"):
            Zone(id="a1b2c3d", name="example.com")

        # ID too long
        with pytest.raises(ValueError, match="Zone ID .* must be a 22-character alphanumeric string"):
            Zone(id="a1b2c3d4e5f6g7h8i9j0k123", name="example.com")

    def test_valid_zone_names(self):
        """Test that valid zone names are accepted."""
        valid_names = [
            "example.com",
            "sub.example.com",
            "example-with-hyphens.com",
            "123numeric.com",
            "xn--bcher-kva.tld",  # IDN domain (bücher.tld)
            "single-label.tld",
            "multi.label.domain.tld",
            "domain.co.uk",  # Multi-part TLD
            "a" * 63 + ".com",  # Maximum length label
        ]

        for name in valid_names:
            zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name=name)
            assert zone.name == name

    def test_invalid_zone_names(self):
        """Test that invalid zone names are rejected."""
        invalid_names = [
            # Non-string name
            123,
            # Empty name
            "",
            # Missing TLD
            "example",
            # Invalid TLD (numeric)
            "example.123",
            # Invalid TLD (single character)
            "example.x",
            # Invalid characters
            "example$.com",
            # Label too long (>63 chars)
            "a" * 64 + ".com",
            # Starts with hyphen
            "-example.com",
            # Ends with hyphen
            "example-.com",
            # Missing label between dots
            "example..com",
            # Trailing dot (FQDN notation) - actually invalid for Hetzner zones
            "example.com.",
        ]

        for name in invalid_names:
            with pytest.raises(ValueError):
                Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name=name)  # type: ignore

    def test_records_list_validation(self):
        """Test validation of the records list."""
        # Valid empty records list
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com")
        assert zone.records == []

        # Valid non-empty records list
        records = [
            Record(id="0123456789abcdef0123456789abcdef", type="A", name="test", value="192.168.1.1"),
            Record(id="0123456789abcdef0123456789abcdef", type="AAAA", name="test", value="2001:db8::1"),
        ]
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)
        assert len(zone.records) == 2

        # Non-list records
        with pytest.raises(ValueError, match="Records must be a list"):
            Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records="not-a-list")  # type: ignore

    def test_duplicate_records_detection(self):
        """Test that duplicate records are rejected."""
        # Create records with same type, name, and value
        records = [
            Record(id="0123456789abcdef0123456789abcdef", type="A", name="test", value="192.168.1.1"),
            Record(id="fedcba9876543210fedcba9876543210", type="A", name="test", value="192.168.1.1"),
        ]

        # Should raise error due to duplicate record
        with pytest.raises(ValueError, match="Duplicate record found"):
            Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)

        # Same name but different types should work
        records = [
            Record(id="0123456789abcdef0123456789abcdef", type="A", name="test", value="192.168.1.1"),
            Record(id="fedcba9876543210fedcba9876543210", type="AAAA", name="test", value="2001:db8::1"),
        ]
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)
        assert len(zone.records) == 2

        # Same type but different names should work
        records = [
            Record(id="0123456789abcdef0123456789abcdef", type="A", name="test1", value="192.168.1.1"),
            Record(id="fedcba9876543210fedcba9876543210", type="A", name="test2", value="192.168.1.1"),
        ]
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)
        assert len(zone.records) == 2

        # Same type and name but different values should work
        records = [
            Record(id="0123456789abcdef0123456789abcdef", type="A", name="test", value="192.168.1.1"),
            Record(id="fedcba9876543210fedcba9876543210", type="A", name="test", value="192.168.1.2"),
        ]
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)
        assert len(zone.records) == 2

    def test_records_sorting(self):
        """Test that records are sorted by type and then name."""
        # Create records in random order
        records = [
            Record(id="10000000000000000000000000000001", type="MX", name="test", value="10 mail.example.com"),
            Record(id="20000000000000000000000000000002", type="A", name="www", value="192.168.1.1"),
            Record(id="30000000000000000000000000000003", type="AAAA", name="test", value="2001:db8::1"),
            Record(id="40000000000000000000000000000004", type="A", name="test", value="192.168.1.2"),
            Record(id="50000000000000000000000000000005", type="CNAME", name="alias", value="target.example.com"),
        ]

        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)

        # Check if records are sorted by type, then name
        expected_order = ["A", "A", "AAAA", "CNAME", "MX"]
        assert [r.type for r in zone.records] == expected_order

        # Check specific ordering - A records should be sorted by name
        assert zone.records[0].type == "A" and zone.records[0].name == "test"
        assert zone.records[1].type == "A" and zone.records[1].name == "www"
