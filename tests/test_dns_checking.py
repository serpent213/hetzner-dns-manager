"""
Integration tests for DNS record checking.

These tests use mocking to avoid actual DNS queries.
"""

import pytest
from unittest.mock import patch, MagicMock

import click
from hdem import Record, Zone, check_dns_record, setup_dns_resolver, check_zone_records


class TestDNSChecking:
    """Test the DNS record checking functionality."""

    @pytest.fixture
    def mock_resolver(self):
        """Fixture to create a mock DNS resolver."""
        resolver = MagicMock()
        return resolver

    @pytest.fixture
    def mock_ctx(self):
        """Fixture to create a mock Click context."""
        ctx = MagicMock(spec=click.Context)
        ctx.exit = MagicMock()
        return ctx

    @patch("hdem.dns.resolver.Resolver")
    def test_setup_dns_resolver(self, mock_resolver_class):
        """Test the setup of a DNS resolver with authoritative nameservers."""
        # Mock the resolver instance
        mock_resolver_instance = MagicMock()
        mock_resolver_class.return_value = mock_resolver_instance

        # Mock the NS and A/AAAA lookups
        mock_ns_answers = MagicMock()
        mock_ns_record = MagicMock()
        mock_ns_record.__str__.return_value = "ns1.example.com."
        mock_ns_answers.__getitem__.return_value = mock_ns_record

        # Mock A record response
        mock_a_answers = MagicMock()
        mock_a_record = MagicMock()
        mock_a_record.__str__.return_value = "192.0.2.1"
        mock_a_answers.__iter__.return_value = [mock_a_record]

        # Configure the resolve method to return our mock responses
        def mock_resolve(name, record_type):
            if name == "example.com" and record_type == "NS":
                return mock_ns_answers
            elif name == "ns1.example.com" and record_type == "A":
                return mock_a_answers
            raise Exception("Unexpected query")

        with patch("hdem.dns.resolver.resolve", side_effect=mock_resolve):
            resolver = setup_dns_resolver("example.com")

            # Verify the resolver was created and configured
            assert resolver.nameservers == ["192.0.2.1"]

    def test_check_a_record_match(self, mock_ctx, mock_resolver):
        """Test checking an A record that matches DNS."""
        # Create test record
        record = Record(id="01234567890123456789012345678901", type="A", name="www", value="192.0.2.1")

        # Mock the DNS response
        mock_answer = MagicMock()
        mock_answer.rrset.ttl = 3600
        mock_rdata = MagicMock()
        mock_rdata.__str__.return_value = "192.0.2.1"
        mock_answer.__iter__.return_value = [mock_rdata]

        # Configure resolver to return our mock response
        mock_resolver.resolve.return_value = mock_answer

        # Check the record
        status, ttl = check_dns_record(mock_ctx, record, "example.com", mock_resolver)

        # Verify results
        assert status == "match"
        assert ttl == 3600
        mock_resolver.resolve.assert_called_once_with("www.example.com", "A")

    def test_check_a_record_mismatch(self, mock_ctx, mock_resolver):
        """Test checking an A record that doesn't match DNS."""
        # Create test record
        record = Record(id="01234567890123456789012345678901", type="A", name="www", value="192.0.2.1")

        # Mock the DNS response with different IP
        mock_answer = MagicMock()
        mock_answer.rrset.ttl = 3600
        mock_rdata = MagicMock()
        mock_rdata.__str__.return_value = "192.0.2.2"  # Different IP
        mock_answer.__iter__.return_value = [mock_rdata]

        # Configure resolver to return our mock response
        mock_resolver.resolve.return_value = mock_answer

        # Check the record
        status, ttl = check_dns_record(mock_ctx, record, "example.com", mock_resolver)

        # Verify results
        assert status == "mismatch"
        assert ttl == 3600
        mock_resolver.resolve.assert_called_once_with("www.example.com", "A")

    def test_check_mx_record_match(self, mock_ctx, mock_resolver):
        """Test checking an MX record that matches DNS."""
        # Create test MX record
        record = Record(id="01234567890123456789012345678901", type="MX", name="@", value="10 mail.example.com.")

        # Mock the DNS response
        mock_answer = MagicMock()
        mock_answer.rrset.ttl = 3600
        mock_rdata = MagicMock()
        mock_rdata.preference = 10
        mock_rdata.exchange.__str__.return_value = "mail.example.com."
        mock_answer.__iter__.return_value = [mock_rdata]

        # Configure resolver to return our mock response
        mock_resolver.resolve.return_value = mock_answer

        # Check the record
        status, ttl = check_dns_record(mock_ctx, record, "example.com", mock_resolver)

        # Verify results
        assert status == "match"
        assert ttl == 3600
        mock_resolver.resolve.assert_called_once_with("example.com", "MX")

    def test_check_txt_record_match(self, mock_ctx, mock_resolver):
        """Test checking a TXT record that matches DNS."""
        # Create test TXT record
        record = Record(
            id="01234567890123456789012345678901",
            type="TXT",
            name="txt",
            value='"v=spf1 include:_spf.example.com ~all"',
        )

        # Mock the DNS response
        mock_answer = MagicMock()
        mock_answer.rrset.ttl = 3600
        mock_rdata = MagicMock()
        # TXT records are returned as a list of strings
        mock_rdata.strings = [b"v=spf1 include:_spf.example.com ~all"]
        mock_answer.__iter__.return_value = [mock_rdata]

        # Configure resolver to return our mock response
        mock_resolver.resolve.return_value = mock_answer

        # Check the record
        status, ttl = check_dns_record(mock_ctx, record, "example.com", mock_resolver)

        # Verify results
        assert status == "match"
        assert ttl == 3600
        mock_resolver.resolve.assert_called_once_with("txt.example.com", "TXT")

    def test_check_cname_record_match(self, mock_ctx, mock_resolver):
        """Test checking a CNAME record that matches DNS."""
        # Create test CNAME record (relative format)
        record = Record(id="01234567890123456789012345678901", type="CNAME", name="alias", value="target")

        # Mock the DNS response
        mock_answer = MagicMock()
        mock_answer.rrset.ttl = 3600
        mock_rdata = MagicMock()
        mock_rdata.__str__.return_value = "target.example.com."
        mock_answer.__iter__.return_value = [mock_rdata]

        # Configure resolver to return our mock response
        mock_resolver.resolve.return_value = mock_answer

        # Check the record
        status, ttl = check_dns_record(mock_ctx, record, "example.com", mock_resolver)

        # Verify results
        assert status == "match"
        assert ttl == 3600
        mock_resolver.resolve.assert_called_once_with("alias.example.com", "CNAME")

    def test_check_missing_record(self, mock_ctx, mock_resolver):
        """Test checking a record that doesn't exist in DNS."""
        # Create test record
        record = Record(id="", type="A", name="nonexistent", value="192.0.2.1")

        # Mock a NXDOMAIN response
        from dns.resolver import NXDOMAIN

        mock_resolver.resolve.side_effect = NXDOMAIN()

        # Check the record
        status, ttl = check_dns_record(mock_ctx, record, "example.com", mock_resolver)

        # Verify results
        assert status == "missing"
        assert ttl is None
        mock_resolver.resolve.assert_called_once_with("nonexistent.example.com", "A")

    @patch("hdem.setup_dns_resolver")
    @patch("hdem.check_dns_record")
    def test_check_zone_records(self, mock_check_dns_record, mock_setup_resolver, mock_ctx):
        """Test checking all records in a zone."""
        # Mock resolver setup
        mock_resolver = MagicMock()
        mock_setup_resolver.return_value = mock_resolver

        # Create test zone with records
        records = [
            Record(id="00000000000000000000000000000001", type="A", name="www", value="192.0.2.1"),
            Record(id="00000000000000000000000000000002", type="MX", name="@", value="10 mail.example.com"),
            Record(id="00000000000000000000000000000003", type="TXT", name="txt", value='"v=spf1 ~all"'),
            Record(
                id="00000000000000000000000000000004",
                type="SOA",
                name="@",
                value="ns1.example.com. hostmaster.example.com. 2023010101 3600 600 86400 3600",
            ),
        ]
        zone = Zone(id="a1b2c3d4e5f6g7h8i9j0k1", name="example.com", records=records)

        # Configure mock responses for each record
        def mock_check_record(ctx, record, zone_name, resolver):
            # SOA records are skipped in check_zone_records
            if record.type == "A":
                return "match", 3600
            elif record.type == "MX":
                return "mismatch", 3600
            elif record.type == "TXT":
                return "mismatch", None  # In the implementation it becomes "mismatch" if record has an ID
            return "unknown", None

        mock_check_dns_record.side_effect = mock_check_record

        # Check the zone records
        result = check_zone_records(mock_ctx, zone, verbose=True)

        # Verify the results
        assert len(result["missing_records"]) == 0  # No missing records

        assert len(result["mismatch_records"]) == 2  # Both MX and TXT are mismatched
        assert any(r.type == "MX" for r in result["mismatch_records"])
        assert any(r.type == "TXT" for r in result["mismatch_records"])

        # SOA records should be skipped
        assert mock_check_dns_record.call_count == 3  # A, MX, TXT (SOA skipped)
