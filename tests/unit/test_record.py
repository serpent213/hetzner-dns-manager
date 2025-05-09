"""
Tests for the Record dataclass.
"""

import ipaddress
import pytest

from hdem import Record


class TestRecordValidation:
    """Test the validation of Record dataclass."""

    def test_valid_record_id(self):
        """Test that valid record IDs are accepted."""
        # Valid 32-character hexadecimal string
        record = Record(id="0123456789abcdef0123456789abcdef", type="A", name="test", value="192.168.1.1")
        assert record.id == "0123456789abcdef0123456789abcdef"

        # Empty ID (for new records)
        record = Record(id="", type="A", name="test", value="192.168.1.1")
        assert record.id == ""

    def test_invalid_record_id(self):
        """Test that invalid record IDs are rejected."""
        # Non-string ID
        with pytest.raises(ValueError, match="Record ID must be a string"):
            Record(
                id=123,  # type: ignore
                type="A",
                name="test",
                value="192.168.1.1",
            )

        # ID with invalid characters
        with pytest.raises(ValueError, match="Record ID .* must be a 32-character hexadecimal string"):
            Record(id="0123456789abcdefGHIJ6789abcdef", type="A", name="test", value="192.168.1.1")

        # ID with wrong length
        with pytest.raises(ValueError, match="Record ID .* must be a 32-character hexadecimal string"):
            Record(id="0123456789abcdef", type="A", name="test", value="192.168.1.1")

    def test_valid_record_types(self):
        """Test that all valid record types are accepted."""
        valid_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "SRV", "CAA", "PTR"]

        for type_ in valid_types:
            # Use a type-appropriate value for each record type
            value = self._get_sample_value_for_type(type_)
            record = Record(id="", type=type_, name="test", value=value)
            assert record.type == type_

    def test_invalid_record_type(self):
        """Test that invalid record types are rejected."""
        # Empty type
        with pytest.raises(ValueError, match="Record type cannot be empty"):
            Record(id="", type="", name="test", value="192.168.1.1")

        # Invalid type
        with pytest.raises(ValueError, match="Invalid record type"):
            Record(id="", type="INVALID", name="test", value="192.168.1.1")

    def test_valid_record_names(self):
        """Test that valid record names are accepted."""
        valid_names = [
            "@",  # Apex/root of zone
            "test",
            "test-with-hyphens",
            "a.subdomain",
            "deep.nested.subdomain",
            "with_underscore",  # Valid for service records per RFC 2181
            "1starts-with-number",
            "a" * 63,  # Maximum length label
            "_service._tcp",  # Service discovery record
        ]

        for name in valid_names:
            record = Record(id="", type="TXT", name=name, value='"test value"')
            assert record.name == name

    def test_invalid_record_names(self):
        """Test that invalid record names are rejected."""
        invalid_names = [
            # Non-string name
            123,
            # Empty name (should use @ for root)
            "",
            # Name with invalid characters
            "test.with.special$chars",
            # Label too long (>63 chars)
            "a" * 64,
            # Starts with hyphen
            "-starts-with-hyphen",
            # Ends with hyphen
            "ends-with-hyphen-",
            # Multiple consecutive hyphens (valid but unusual)
            # "test--double-hyphen"  # Actually valid per DNS specs
        ]

        for name in invalid_names:
            with pytest.raises(ValueError):
                Record(id="", type="TXT", name=name, value='"test value"')  # type: ignore

    def test_invalid_empty_value(self):
        """Test that empty values are rejected."""
        with pytest.raises(ValueError, match="Record value cannot be empty"):
            Record(id="", type="A", name="test", value="")

    def test_a_record_validation(self):
        """Test validation of A records (IPv4 addresses)."""
        # Valid IPv4 addresses
        valid_ips = ["192.168.1.1", "127.0.0.1", "0.0.0.0", "255.255.255.255", "8.8.8.8"]

        for ip in valid_ips:
            record = Record(id="", type="A", name="test", value=ip)
            assert record.value == ip
            # Verify it's a valid IPv4 address by parsing with ipaddress module
            assert ipaddress.IPv4Address(ip)

        # Invalid IPv4 addresses
        invalid_ips = [
            "256.0.0.1",  # Out of range
            "192.168.1",  # Missing octet
            "192.168.1.1.5",  # Too many octets
            "192.168.1.a",  # Non-numeric
            "2001:db8::1",  # IPv6 address
            "not-an-ip",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValueError, match="Invalid IPv4 address for A record"):
                Record(id="", type="A", name="test", value=ip)

    def test_aaaa_record_validation(self):
        """Test validation of AAAA records (IPv6 addresses)."""
        # Valid IPv6 addresses
        valid_ips = [
            "2001:db8::1",
            "::1",
            "::",
            "2001:0db8:0000:0000:0000:0000:0000:0001",
            "2001:db8::1:0:0:1",
            "fe80::1ff:fe23:4567:890a",
        ]

        for ip in valid_ips:
            record = Record(id="", type="AAAA", name="test", value=ip)
            assert record.value == ip
            # Verify it's a valid IPv6 address by parsing with ipaddress module
            assert ipaddress.IPv6Address(ip)

        # Invalid IPv6 addresses
        invalid_ips = [
            "2001:db8::1::2",  # Multiple :: segments
            "2001:db8:g::1",  # Invalid hex
            "192.168.1.1",  # IPv4 address
            "not-an-ip",
            "2001:db8::1::",  # Trailing ::
            "::db8::1",  # Multiple :: segments
        ]

        for ip in invalid_ips:
            with pytest.raises(ValueError, match="Invalid IPv6 address for AAAA record"):
                Record(id="", type="AAAA", name="test", value=ip)

    def test_mx_record_validation(self):
        """Test validation of MX records."""
        # Valid MX records
        valid_mx = [
            "10 mail.example.com",
            "0 mail.example.com.",
            "5 mail.example.com",
            "65535 mail.example.com",
            "1 mail-server",
        ]

        for mx in valid_mx:
            record = Record(id="", type="MX", name="test", value=mx)
            assert record.value == mx

        # Invalid MX records
        invalid_mx = [
            "mail.example.com",  # Missing priority
            "mail.example.com 10",  # Reversed format
            "-5 mail.example.com",  # Negative priority
            "65536 mail.example.com",  # Priority too high
            "10",  # Missing hostname
            "TEN mail.example.com",  # Non-numeric priority
            "10  ",  # Missing hostname with space
            "10 mail.example.com 20",  # Extra value
        ]

        for mx in invalid_mx:
            with pytest.raises(ValueError):
                Record(id="", type="MX", name="test", value=mx)

    def test_txt_record_validation(self):
        """Test validation of TXT records."""
        # Valid TXT records
        valid_txt = [
            '"This is a TXT record"',
            '"v=spf1 include:_spf.example.com ~all"',
            '"This is a" "multi-part TXT record"',
            '"Contains \\"escaped\\" quotes"',
        ]

        for txt in valid_txt:
            record = Record(id="", type="TXT", name="test", value=txt)
            assert record.value == txt

        # Invalid TXT records
        invalid_txt = [
            "This is not quoted",
            'No end quote"',
            '"No start quote',
            '"',  # Single quote
            "",  # Empty value
        ]

        for txt in invalid_txt:
            with pytest.raises(ValueError):
                Record(id="", type="TXT", name="test", value=txt)

    def test_soa_record_validation(self):
        """Test validation of SOA records."""
        # Valid SOA record
        valid_soa = "ns1.example.com. admin.example.com. 2023010101 3600 600 1209600 86400"
        record = Record(id="", type="SOA", name="@", value=valid_soa)
        assert record.value == valid_soa

        # Invalid SOA records
        invalid_soa = [
            # Missing components
            "ns1.example.com. admin.example.com. 2023010101",
            # Non-numeric serial, refresh, retry, expire, or minimum
            "ns1.example.com. admin.example.com. serial 3600 600 1209600 86400",
            # Too many components
            "ns1.example.com. admin.example.com. 2023010101 3600 600 1209600 86400 extra",
        ]

        for soa in invalid_soa:
            with pytest.raises(ValueError):
                Record(id="", type="SOA", name="@", value=soa)

    def test_cname_record_validation(self):
        """Test validation of CNAME records."""
        # Valid CNAME targets
        valid_cnames = [
            "example.com",
            "example.com.",  # With trailing dot
            "sub.example.com",
            "host",
            "sub.domain.example.com.",
            "a-valid-hostname",
            "host123",
        ]

        for cname in valid_cnames:
            record = Record(id="", type="CNAME", name="test", value=cname)
            assert record.value == cname

        # Invalid CNAME targets
        invalid_cnames = [
            "",  # Empty value
            "invalid.host.name$",  # Invalid characters
            "domain.with-trailing-hyphen-.",  # Trailing hyphen in label
            "-domain.with-leading-hyphen",  # Leading hyphen in label
            # Label too long (>63 chars)
            "a" * 64 + ".example.com",
        ]

        for cname in invalid_cnames:
            with pytest.raises(ValueError):
                Record(id="", type="CNAME", name="test", value=cname)

    def _get_sample_value_for_type(self, record_type):
        """Helper method to get valid test values for each record type."""
        values = {
            "A": "192.168.1.1",
            "AAAA": "2001:db8::1",
            "CNAME": "example.com",
            "MX": "10 mail.example.com",
            "TXT": '"This is a TXT record"',
            "NS": "ns1.example.com",
            "SOA": "ns1.example.com. admin.example.com. 2023010101 3600 600 1209600 86400",
            "SRV": "0 5 5060 sip.example.com",  # SRV records have no specific validation yet
            "CAA": '0 issue "letsencrypt.org"',  # CAA records have no specific validation yet
            "PTR": "host.example.com.",  # PTR records have no specific validation yet
        }
        return values.get(record_type, "default-value")
