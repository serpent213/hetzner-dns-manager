"""
Tests for helper functions in the hdem module.
"""

from hdem import process_txt_record_value, get_expected_hostname


class TestTxtRecordProcessing:
    """Test the TXT record processing helper function."""

    def test_concat_txt_records(self):
        """Test concatenation of segmented TXT record values."""
        # Single part, no change needed
        assert process_txt_record_value('"Simple TXT value"') == '"Simple TXT value"'

        # Multi-part values - the implementation keeps spaces between the parts
        assert process_txt_record_value('"First part" "Second part"') == '"First partSecond part"'
        assert process_txt_record_value('"Part 1" "Part 2" "Part 3"') == '"Part 1Part 2Part 3"'

        # With special characters and quotes
        assert (
            process_txt_record_value('"Contains \\"quotes\\"" " and spaces"') == '"Contains \\"quotes\\" and spaces"'
        )

        # Non-quoted value shouldn't be modified
        assert process_txt_record_value("Not quoted") == "Not quoted"

        # Empty value
        assert process_txt_record_value('""') == '""'

    def test_no_concat_txt_records(self):
        """Test disabling concatenation (preserve original format)."""
        # When concat=False, values should be preserved as-is
        assert process_txt_record_value('"First part" "Second part"', concat=False) == '"First part" "Second part"'
        assert process_txt_record_value('"Simple TXT value"', concat=False) == '"Simple TXT value"'


class TestHostnameFormatting:
    """Test the hostname formatting helper function."""

    def test_absolute_hostnames(self):
        """Test handling of absolute hostnames (with trailing dot)."""
        # Absolute hostname (with trailing dot) should have dot removed
        assert get_expected_hostname("mail.example.com.", "example.org") == "mail.example.com"
        assert get_expected_hostname("example.com.", "example.org") == "example.com"

        # Ensure zones with different name don't affect absolute hostnames
        assert get_expected_hostname("service.other-domain.com.", "example.com") == "service.other-domain.com"

    def test_relative_hostnames(self):
        """Test handling of relative hostnames (without trailing dot)."""
        # Relative hostname should have zone name appended
        assert get_expected_hostname("mail", "example.com") == "mail.example.com"
        assert get_expected_hostname("www", "example.org") == "www.example.org"

        # Multi-part hostnames
        assert get_expected_hostname("sub.domain", "example.com") == "sub.domain.example.com"
