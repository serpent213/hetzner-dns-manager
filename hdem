#!/usr/bin/env -S uv run --script --quiet
# -*- mode: python -*-
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click",
#     "dnspython",
#     "ipaddress",
#     "requests",
#     "rich",
#     "ruamel.yaml",
# ]
# ///
"""
Hetzner DNS Manager

A command-line tool for managing Hetzner DNS records with a local YAML database.
Allows importing, checking, updating, and deleting DNS records.

Designed and implemented in 2025 by Steffen Beyer (and Claude Code).
"""

import ipaddress
import os
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, cast

import click
import dns.resolver
import requests
from rich.console import Console
from rich.table import Table
from ruamel.yaml import YAML

# Constants
VERSION = "0.1.0"
API_BASE_URL = "https://dns.hetzner.com/api/v1"
ZONES_DIR = pathlib.Path("./zones")


# Define TypedDict classes for API responses
class ZoneData(TypedDict):
    id: str
    name: str


class ZoneResponse(TypedDict):
    zones: List[ZoneData]


class RecordData(TypedDict):
    id: str
    zone_id: str
    type: str
    name: str
    value: str


class RecordCreateRequest(TypedDict):
    zone_id: str
    type: str
    name: str
    value: str


class RecordUpdateRequest(TypedDict):
    id: str
    zone_id: str
    type: str
    name: str
    value: str


class BulkRecordResponse(TypedDict):
    records: List[RecordData]
    invalid_records: Optional[List[RecordData]]
    failed_records: Optional[List[RecordData]]


# Record type literal for type checking
RecordType = Literal["A", "AAAA", "CNAME", "MX", "TXT", "NS", "SOA", "SRV", "CAA", "PTR"]


# DNS validation regex patterns
# Single DNS label (RFC 1035) - one component of a domain name
DNS_LABEL_REGEX: str = r"[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
# DNS label with underscore support (RFC 2181) - for service records
SERVICE_LABEL_REGEX: str = r"[a-zA-Z0-9_]([a-zA-Z0-9_\-]{0,61}[a-zA-Z0-9_])?"
# Top-level domain pattern - alphabetic with at least 2 chars
TLD_REGEX: str = r"[a-zA-Z]{2,}"
# Public zone name pattern - requires valid TLD at the end (for Hetzner)
PUBLIC_ZONE_REGEX: str = f"^({DNS_LABEL_REGEX}\\.)+{TLD_REGEX}$"
# Domain name with optional trailing dot (FQDN or relative notation)
FQDN_OR_RELATIVE_REGEX: str = f"^{DNS_LABEL_REGEX}(\\.{DNS_LABEL_REGEX})*\\.?$"


# Global setup
ZONES_DIR.mkdir(exist_ok=True)
API_TOKEN: Optional[str] = os.environ.get("HETZNER_DNS_API_TOKEN")
console: Console = Console()


@dataclass
class Record:
    """DNS Record data structure with validation."""

    id: str
    type: RecordType
    name: str
    value: str

    def __post_init__(self):
        """Validate record fields strictly based on DNS standards."""
        # Validate ID - should be a hexadecimal string of specific length or empty for new records
        if self.id:
            if not isinstance(self.id, str):
                raise ValueError("Record ID must be a string")

            # Hetzner record IDs are 32-char hex strings
            if not re.match(r"^[0-9a-f]{32}$", self.id):
                raise ValueError(f"Record ID '{self.id}' must be a 32-character hexadecimal string")

        # Validate record type
        if not self.type:
            raise ValueError("Record type cannot be empty")

        valid_record_types = [
            "A",
            "AAAA",
            "CNAME",
            "MX",
            "TXT",
            "NS",
            "SOA",
            "SRV",
            "CAA",
            "PTR",
        ]
        if self.type not in valid_record_types:
            raise ValueError(f"Invalid record type: {self.type}. Must be one of {', '.join(valid_record_types)}")

        if not isinstance(self.name, str):
            raise ValueError("Record name must be a string")

        # Validate record name according to RFC 1035, plus allow underscores for service records (RFC 2181)
        # Allow @ as shorthand for apex/root of zone
        if self.name != "@":
            record_name_regex = f"^({SERVICE_LABEL_REGEX}\\.)*{SERVICE_LABEL_REGEX}$"
            if not re.match(record_name_regex, self.name):
                raise ValueError(f"Invalid record name format: {self.name}")

        if not self.value:
            raise ValueError("Record value cannot be empty")

        # Type-specific validation
        match self.type:
            case "A":
                # IPv4 address validation
                try:
                    ipaddress.IPv4Address(self.value)
                except ValueError:
                    raise ValueError(f"Invalid IPv4 address for A record: {self.value}")

            case "AAAA":
                # IPv6 address validation
                try:
                    ipaddress.IPv6Address(self.value)
                except ValueError:
                    raise ValueError(f"Invalid IPv6 address for AAAA record: {self.value}")

            case "MX":
                # MX records should have format "priority hostname"
                if not re.match(r"^\d+\s+\S+$", self.value):
                    raise ValueError(
                        f"Invalid MX record format: {self.value}. Expected format: '10 mail.example.com.'"
                    )

                # Extract priority and check if it's within valid range (0-65535)
                try:
                    priority = int(self.value.split()[0])
                    if priority < 0 or priority > 65535:
                        raise ValueError(f"Invalid MX priority: {priority}. Must be between 0 and 65535")
                except (ValueError, IndexError):
                    raise ValueError(f"Invalid MX priority in record: {self.value}")

            case "TXT":
                # TXT records should be quoted
                if not (self.value.startswith('"') and (self.value.endswith('"') or ' "' in self.value)):
                    raise ValueError(f"Invalid TXT record format: {self.value}. Value should be quoted")

            case "SOA":
                # SOA records have a specific format with 7 parts
                parts = self.value.split(" ")
                if len(parts) != 7:
                    raise ValueError(
                        f"Invalid SOA record format: {self.value}. Expected format: 'primary_ns admin_email serial refresh retry expire minimum'"
                    )

                # Check if the serial, refresh, retry, expire, and minimum are numeric
                for i in range(2, 7):
                    try:
                        int(parts[i])
                    except ValueError:
                        raise ValueError(
                            "Invalid SOA record: numeric values required for serial, refresh, retry, expire, and minimum"
                        )

            case "CNAME":
                # CNAME records should point to a hostname
                if not self.value:
                    raise ValueError("CNAME record value cannot be empty")

                if not re.match(FQDN_OR_RELATIVE_REGEX, self.value):
                    raise ValueError(f"Invalid hostname format for CNAME record: {self.value}")

            case _:
                # Other record types have no specific validation beyond the basic checks above
                pass


@dataclass
class Zone:
    """DNS Zone data structure with validation."""

    id: str
    name: str
    records: List[Record] = field(default_factory=list)

    def __post_init__(self):
        """Validate zone fields strictly according to Hetzner DNS standards."""
        # Validate ID
        if not isinstance(self.id, str):
            raise ValueError("Zone ID must be a string")

        if not self.id:
            raise ValueError("Zone ID cannot be empty")

        # Hetzner zone IDs are 21- or 22-character alphanumeric strings
        if not re.match(r"^[a-zA-Z0-9]{21,22}$", self.id):
            raise ValueError(f"Zone ID '{self.id}' must be a 22-character alphanumeric string")

        # Validate zone name (domain name)
        if not isinstance(self.name, str):
            raise ValueError("Zone name must be a string")

        if not self.name:
            raise ValueError("Zone name cannot be empty")

        # Hetzner DNS only supports public domains with proper TLDs
        if not re.match(PUBLIC_ZONE_REGEX, self.name):
            raise ValueError(f"Invalid domain name format for zone: {self.name}")

        # Validate records list
        if not isinstance(self.records, list):
            raise ValueError("Records must be a list")

        # Check for duplicate records (same type, name, and value)
        record_keys = set()
        for record in self.records:
            key = (record.type, record.name, record.value)
            if key in record_keys:
                raise ValueError(f"Duplicate record found: {record.type} {record.name} {record.value}")
            record_keys.add(key)

        # Sort records by type, then name
        self.records.sort(key=lambda r: (r.type, r.name))


class HetznerDNSClient:
    """Client for interacting with the Hetzner DNS API."""

    def __init__(self, api_token: str, dry_run: bool = False) -> None:
        self.api_token: str = api_token
        self.headers: Dict[str, str] = {
            "Auth-API-Token": api_token,
            "Content-Type": "application/json",
        }
        self.dry_run: bool = dry_run

    def _dry_run_handler(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle API request in dry run mode."""
        console.print("\n[bold]Dry run - API request that would be sent:[/]")
        console.print(f"{method.upper()} {url}" + (f"?{params}" if params else ""))
        console.print("Headers: {'Auth-API-Token': '***', 'Content-Type': 'application/json'}")
        if json:
            console.print(f"Payload: {json}")
        sys.exit(0)

    def make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request with pattern matching for HTTP methods."""
        if self.dry_run:
            self._dry_run_handler(method, url, params, json)

        try:
            match method.lower():
                case "get":
                    response = requests.get(url, params=params, headers=self.headers)
                case "post":
                    response = requests.post(url, headers=self.headers, json=json)
                case "put":
                    response = requests.put(url, headers=self.headers, json=json)
                case "delete":
                    response = requests.delete(url, headers=self.headers)
                case _:
                    raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            sys.exit(1)

    def get_all_zones(self) -> ZoneResponse:
        """Get all zones from the API."""
        url = f"{API_BASE_URL}/zones"
        return cast(ZoneResponse, self.make_request("get", url))

    def get_zone_records(self, zone_id: str) -> Dict[str, List[RecordData]]:
        """Get all records for a specific zone."""
        url = f"{API_BASE_URL}/records"
        params = {"zone_id": zone_id}
        return self.make_request("get", url, params)

    def delete_record(self, record_id: str) -> Dict[str, Any]:
        """Delete a specific record."""
        url = f"{API_BASE_URL}/records/{record_id}"
        return self.make_request("delete", url)

    def bulk_update_records(self, records: List[RecordUpdateRequest]) -> BulkRecordResponse:
        """Update multiple records at once."""
        url = f"{API_BASE_URL}/records/bulk"
        payload = {"records": records}
        return cast(BulkRecordResponse, self.make_request("put", url, json=payload))

    def bulk_create_records(self, records: List[RecordCreateRequest]) -> BulkRecordResponse:
        """Create multiple records at once."""
        url = f"{API_BASE_URL}/records/bulk"
        payload = {"records": records}
        return cast(BulkRecordResponse, self.make_request("post", url, json=payload))


class YAMLHandler:
    """Handler for YAML file operations."""

    def __init__(self) -> None:
        self.yaml = YAML()
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.yaml.preserve_quotes = True

    def read_zone(self, domain: str) -> Optional[Zone]:
        """Read a zone file from disk."""
        file_path = ZONES_DIR / f"{domain}.yaml"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = self.yaml.load(f)

        zone = Zone(id=data["id"], name=data["name"], records=[])

        for record_data in data.get("records", []):
            # Cast the record type to RecordType
            record_type = cast(RecordType, record_data["type"])
            record = Record(
                id=record_data["id"],
                type=record_type,
                name=record_data["name"],
                value=record_data["value"],
            )
            zone.records.append(record)

        zone.records.sort(key=lambda r: (r.type, r.name))

        return zone

    def write_zone(self, zone: Zone) -> pathlib.Path:
        """Write a zone file to disk."""
        file_path = ZONES_DIR / f"{zone.name}.yaml"

        data = {
            "id": zone.id,
            "name": zone.name,
            "records": [
                {
                    "id": record.id,
                    "type": record.type,
                    "name": record.name,
                    "value": record.value,
                }
                for record in sorted(zone.records, key=lambda r: (r.type, r.name))
            ],
        }

        with open(file_path, "w") as f:
            self.yaml.dump(data, f)

        return file_path


def get_expected_hostname(hostname: str, zone_name: str) -> str:
    """
    Format hostname for DNS comparisons based on record format.

    Args:
        hostname: Record hostname (may be absolute with trailing dot or relative)
        zone_name: Zone/domain name for constructing FQDN

    Returns:
        Formatted hostname expected in DNS responses (without trailing dot)
    """
    # Check if this is an absolute hostname (ends with dot)
    if hostname.endswith("."):
        return hostname.rstrip(".")
    else:
        # It's a relative hostname, so append the zone name
        return f"{hostname}.{zone_name}"


def check_dns_record(record: Record, zone_name: str) -> str:
    """
    Verify if a DNS record matches its actual DNS entry using authoritative servers.

    Args:
        record: Record object to check against DNS
        zone_name: Zone/domain name the record belongs to

    Returns:
        Status string: 'match', 'mismatch', or 'missing'
    """
    resolver = dns.resolver.Resolver()

    # First, get the authoritative nameservers for this domain
    try:
        ns_answers = dns.resolver.resolve(zone_name, "NS")
        if ns_answers:
            # Set the first authoritative nameserver as our resolver
            auth_ns = str(ns_answers[0]).rstrip(".")

            nameserver_ips = []

            # Try IPv4 first
            try:
                a_records = dns.resolver.resolve(auth_ns, "A")
                for a_record in a_records:
                    nameserver_ips.append(str(a_record))
            except Exception:
                pass

            # Try IPv6 if available
            try:
                aaaa_records = dns.resolver.resolve(auth_ns, "AAAA")
                for aaaa_record in aaaa_records:
                    nameserver_ips.append(str(aaaa_record))
            except Exception:
                pass

            # If we got any nameserver IPs, use them
            if nameserver_ips:
                resolver.nameservers = nameserver_ips
    except Exception:
        # If we can't get authoritative nameservers, continue with default resolver
        pass

    try:
        # Handle domain name formatting
        if record.name == "@":
            query_name = zone_name
        else:
            query_name = f"{record.name}.{zone_name}"

        # Try to resolve the record to detect if it exists
        try:
            answers = resolver.resolve(query_name, record.type)

            match record.type:
                case "MX":
                    # MX records have priority and hostname, e.g., "10 mail.example.com."
                    priority, host = record.value.split(" ", 1)
                    priority_int = int(priority)

                    # Get expected hostname based on whether it's absolute or relative
                    expected_host = get_expected_hostname(host, zone_name)

                    for rdata in answers:
                        rdata_host = str(getattr(rdata, "exchange")).rstrip(".")
                        rdata_pref = getattr(rdata, "preference")

                        if rdata_host == expected_host and rdata_pref == priority_int:
                            return "match"

                    return "mismatch"

                case "TXT":
                    # Get the TXT record value from YAML
                    yaml_value = record.value

                    # Remove quotes if they are included in the YAML value
                    if yaml_value.startswith('"') and yaml_value.endswith('"'):
                        yaml_value = yaml_value[1:-1]

                    # Handle multi-part TXT records with spaces between quoted parts
                    yaml_value = yaml_value.replace('" "', "")

                    # Check if any of the returned TXT records match our expected value
                    for rdata in answers:
                        # DNSPython returns TXT records as bytes objects in a list
                        # First join all segments together
                        strings = getattr(rdata, "strings", [])
                        dns_value = "".join(str(t) for t in strings)

                        # Remove any 'b' prefixes that might appear in string representation of bytes
                        dns_value = dns_value.replace("b'", "").replace("'", "")

                        if dns_value == yaml_value:
                            return "match"

                    return "mismatch"

                case "CNAME":
                    expected_target = get_expected_hostname(record.value, zone_name)

                    for rdata in answers:
                        dns_target = str(rdata).rstrip(".")  # Remove trailing dot if present

                        if dns_target == expected_target:
                            return "match"

                    return "mismatch"

                case "NS":
                    expected_ns = get_expected_hostname(record.value, zone_name)

                    for rdata in answers:
                        dns_ns = str(rdata).rstrip(".")  # Remove trailing dot

                        if dns_ns == expected_ns:
                            return "match"

                    return "mismatch"

                case _:
                    # For other record types (A, AAAA, etc.)
                    for rdata in answers:
                        if str(rdata) == record.value:
                            return "match"

                    return "mismatch"

        except dns.resolver.NXDOMAIN:
            # Domain doesn't exist
            return "missing"
        except dns.resolver.NoAnswer:
            # No answer from DNS for this record type
            return "missing"

    except dns.resolver.NoNameservers:
        # No nameservers could be reached
        console.print(
            f"[bold red]Error:[/] checking DNS for {record.name}.{zone_name} ({record.type}): No nameservers could be reached"
        )
        sys.exit(1)

    except Exception as e:
        # Any other error
        console.print(f"[bold red]Error:[/] checking DNS for {record.name}.{zone_name} ({record.type}): {e}")
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option(
    "--dry",
    is_flag=True,
    help="Print the first API request that would be performed and then halt",
)
@click.option(
    "--version",
    is_flag=True,
    help="Show the version and exit",
)
@click.pass_context
def cli(ctx: click.Context, dry: bool, version: bool) -> None:
    """
    Hetzner DNS Manager - Manage DNS records with Hetzner DNS API and local YAML database.

    Stores one YAML file per zone in the "./zones" directory. Provides commands for importing,
    checking, updating, and deleting DNS records.

    Requires HETZNER_DNS_API_TOKEN environment variable to be set to a valid API token.
    """
    if version:
        click.echo(f"{VERSION} (hdem)")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)

    if not API_TOKEN:
        console.print("[bold red]Error:[/] HETZNER_DNS_API_TOKEN environment variable is not set.")
        sys.exit(1)

    ctx.ensure_object(dict)

    # Create API client and store in context
    client = HetznerDNSClient(API_TOKEN, dry_run=dry)
    ctx.obj["client"] = client


@cli.command("import")
@click.argument("domain", required=False)
@click.option("--all", is_flag=True, help="Import all zones")
@click.option("--no-txt-concat", is_flag=True, help="Don't concatenate TXT record values")
@click.option(
    "--force",
    is_flag=True,
    help="Force overwrite existing zone files without confirmation",
)
@click.pass_context
def import_zones(
    ctx: click.Context,
    domain: Optional[str],
    all: bool,
    no_txt_concat: bool,
    force: bool,
) -> None:
    """
    Import zones and records from the Hetzner DNS API.

    Specify a domain name to import a single zone, or use --all to import all zones.

    By default, TXT record values with multiple quoted parts (e.g., '"abc" "def"') will be
    concatenated into a single quoted value (e.g., '"abcdef"'). Use --no-txt-concat to
    disable this behavior.

    If a zone file already exists, you'll be prompted for confirmation before overwriting.
    Use --force to skip confirmation and overwrite existing files.
    """
    yaml_handler = YAMLHandler()
    client = ctx.obj["client"]

    try:
        zones_data = client.get_all_zones()
        zones = zones_data.get("zones", [])

        if not zones:
            console.print("[yellow]No zones found in your Hetzner DNS account.[/]")
            return

        if all:
            # Import all zones
            for zone_data in zones:
                import_single_zone(zone_data, client, yaml_handler, no_txt_concat, force)

        elif domain:
            # Import specific zone
            zone_data = next((z for z in zones if z["name"] == domain), None)

            if not zone_data:
                console.print(f"[bold red]Error:[/] Domain '{domain}' not found in your Hetzner DNS account.")
                return

            import_single_zone(zone_data, client, yaml_handler, no_txt_concat, force)

        else:
            console.print("[bold yellow]Please specify a domain or use --all flag.[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


@cli.command("check")
@click.argument("domain", required=False)
@click.option("--all", is_flag=True, help="Check all zones")
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed output for all zones, including those without errors",
)
@click.pass_context
def check_zones(ctx: click.Context, domain: Optional[str], all: bool, verbose: bool) -> None:
    """
    Check DNS records against actual DNS entries.

    Specify a domain name to check a single zone, or use --all to check all zones.

    Note: Will not catch additional entries that are missing from the local database!
    """
    yaml_handler = YAMLHandler()
    found_issues = False

    try:
        if all:
            # Check all zones

            # For proper spacing using newlines
            newline_before_next_zone = False

            for file_path in ZONES_DIR.glob("*.yaml"):
                domain_name = file_path.stem
                zone = yaml_handler.read_zone(domain_name)
                if zone:
                    if newline_before_next_zone:
                        console.print("")

                    result = check_zone_records(zone, verbose)
                    if result["missing_records"] or result["mismatch_records"]:
                        found_issues = True

                    newline_before_next_zone = verbose or found_issues

            if found_issues:
                sys.exit(1)

        elif domain:
            # Check specific zone
            zone = yaml_handler.read_zone(domain)

            if not zone:
                console.print(f"[bold red]Error:[/] Domain '{domain}' not found in local database.")
                sys.exit(1)

            result = check_zone_records(zone, verbose)
            if result["missing_records"] or result["mismatch_records"]:
                sys.exit(1)

        else:
            console.print("[bold yellow]Please specify a domain or use --all flag.[/]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


def process_txt_record_value(value: str, concat: bool = True) -> str:
    """
    Normalize TXT record values for consistency.

    Args:
        value: Original TXT record value
        concat: If True, concatenate segmented values ('"abc" "def"' → '"abcdef"')

    Returns:
        Processed TXT record value
    """
    if not concat or not value.startswith('"') or '"' not in value[1:]:
        return value

    # Extract content from quoted parts and concatenate
    # Match patterns like "abc" "def" "ghi"
    parts = re.findall(r'"([^"]*)"', value)
    if parts:
        return f'"{("").join(parts)}"'

    return value


def import_single_zone(
    zone_data: ZoneData,
    client: HetznerDNSClient,
    yaml_handler: YAMLHandler,
    no_txt_concat: bool = False,
    force: bool = False,
) -> Optional[pathlib.Path]:
    """
    Import a single zone from Hetzner DNS API to local YAML storage.

    Args:
        zone_data: Dict with zone metadata from API response
        client: HetznerDNSClient instance for API communication
        yaml_handler: YAMLHandler instance for file operations
        no_txt_concat: If True, preserve segmented TXT record format
        force: If True, overwrite existing zone files without prompting

    Returns:
        Path to the saved YAML file or None if import was canceled
    """
    zone_id = zone_data["id"]
    zone_name = zone_data["name"]

    console.print(f"Importing zone: [bold]{zone_name}[/]")

    # Check if zone file already exists
    file_path = ZONES_DIR / f"{zone_name}.yaml"
    if file_path.exists() and not force:
        existing_zone = yaml_handler.read_zone(zone_name)
        if existing_zone:
            console.print(f"[yellow]Zone file already exists:[/] {file_path}")
            console.print(f"Existing file contains [bold]{len(existing_zone.records)}[/] records.")

            if not click.confirm("Do you want to overwrite the existing file?", default=False):
                console.print("[yellow]Import canceled for this zone.[/]")
                return None

    records_data = client.get_zone_records(zone_id)

    zone = Zone(id=zone_id, name=zone_name, records=[])

    # Add records to zone
    for record_data in records_data.get("records", []):
        value = record_data["value"]
        record_type = cast(RecordType, record_data["type"])

        if record_type == "TXT":
            value = process_txt_record_value(value, not no_txt_concat)

        record = Record(
            id=record_data["id"],
            type=record_type,
            name=record_data["name"],
            value=value,
        )
        zone.records.append(record)

    # Save zone to file
    file_path = yaml_handler.write_zone(zone)
    console.print(f"Saved to: [green]{file_path}[/] with [bold]{len(zone.records)}[/] records.")

    return file_path


def check_zone_records(zone: Zone, verbose: bool = False) -> Dict[str, List[Record]]:
    """
    Verify all zone records against live DNS and display comparison results.

    Args:
        zone: Zone object containing records to check
        verbose: If True, show detailed output for all zones, including those without errors

    Returns:
        Dict with missing_records and mismatch_records lists
    """
    # Track missing and mismatched records
    missing_records = []
    mismatch_records = []

    table = Table(show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Local Value", style="blue")
    table.add_column("Status", style="bold")

    for record in zone.records:
        # Skip SOA records as they're modified by Hetzner upon update
        if record.type == "SOA":
            continue

        status_code = check_dns_record(record, zone.name)

        # If the record has an id, we assume a rename
        if status_code == "missing" and record.id:
            status_code = "mismatch"

        match status_code:
            case "match":
                status = "[green]✓ Match[/]"
            case "mismatch":
                status = "[red]✗ Mismatch[/]"
                mismatch_records.append(record)
            case "missing":
                status = "[red]✗ Missing[/]"
                missing_records.append(record)
            case _:
                status = f"[yellow]? Unknown ({status_code})[/]"

        table.add_row(record.type, record.name, record.value, status)

    has_issues = bool(missing_records or mismatch_records)

    # Only print output if there are issues or verbose mode is enabled
    if has_issues or verbose:
        console.print(f"[bold]Checking zone:[/] {zone.name}")
        console.print(table)

        if not has_issues:
            console.print("[green]All records match the DNS entries.[/]")
        else:
            if mismatch_records:
                console.print("[yellow]Some records do not match the DNS entries.[/]")
            if missing_records:
                console.print("[yellow]Some records are missing from DNS.[/]")
    elif not verbose and not has_issues:
        # In non-verbose mode with no issues, just print a simple message
        console.print(f"[green]Zone {zone.name}: All records match.[/]")

    return {"missing_records": missing_records, "mismatch_records": mismatch_records}


@cli.command("delete")
@click.argument("domain", required=True)
@click.argument("record_names", required=True, nargs=-1)
@click.pass_context
def delete_record_cmd(ctx: click.Context, domain: str, record_names: Tuple[str, ...]) -> None:
    """
    Delete one or more DNS records.

    Requires a domain name and one or more record names.
    """
    yaml_handler = YAMLHandler()
    client = ctx.obj["client"]

    try:
        zone = yaml_handler.read_zone(domain)

        if not zone:
            console.print(f"[bold red]Error:[/] Domain '{domain}' not found in local database.")
            sys.exit(1)

        # Process each record name and handle multiple records with the same name
        records_to_delete = []
        missing_names = []

        for record_name in record_names:
            matching_records = [r for r in zone.records if r.name == record_name]

            if not matching_records:
                missing_names.append(record_name)
                continue

            if len(matching_records) == 1:
                # Only one record with this name
                record = matching_records[0]
                console.print(f"Found record: [bold]{record.type}[/] [green]{record_name}[/] [blue]{record.value}[/]")

                if click.confirm("Delete this record?", default=False):
                    records_to_delete.append(record)
            else:
                # Multiple records with the same name
                console.print(f"Found [bold]{len(matching_records)}[/] records with name '{record_name}':")

                # Ask for confirmation for each record
                for record in matching_records:
                    console.print(f"  - [bold]{record.type}[/] [green]{record_name}[/] [blue]{record.value}[/]")

                    if click.confirm("Delete this record?", default=False):
                        records_to_delete.append(record)

        # If any records weren't found, show warning but continue
        if missing_names:
            console.print(f"[bold yellow]Warning:[/] The following record(s) were not found in zone '{domain}':")
            for name in missing_names:
                console.print(f"  - {name}")

            # If no records were found at all, exit
            if not records_to_delete:
                console.print("\n[yellow]No records to delete. Exiting.[/]")
                sys.exit(0)

        # If no records were selected for deletion
        if not records_to_delete:
            console.print("\n[yellow]No records selected for deletion.[/]")
            sys.exit(0)

        # Display summary of records to be deleted
        console.print(f"\n[bold]Summary:[/] {len(records_to_delete)} record(s) selected for deletion:")
        for record in records_to_delete:
            console.print(f"  - [bold]{record.type}[/] [green]{record.name}[/] [blue]{record.value}[/]")

        # Final confirmation before proceeding with API calls
        if not click.confirm("Proceed with deletion?", default=False):
            console.print("[yellow]Deletion canceled.[/]")
            sys.exit(0)

        # Delete records from API
        deleted_record_ids = []
        failed_deletions = []

        for record in records_to_delete:
            try:
                client.delete_record(record.id)
                deleted_record_ids.append(record.id)
            except Exception as e:
                failed_deletions.append((record, str(e)))

        # Report results
        if deleted_record_ids:
            console.print(f"[green]Successfully deleted {len(deleted_record_ids)} record(s) from Hetzner DNS.[/]")

        if failed_deletions:
            console.print(f"[bold red]Failed to delete {len(failed_deletions)} record(s):[/]")
            for record, error in failed_deletions:
                display_name = record.name
                console.print(f"  - {record.type} {display_name}: {error}")

        # Ask user to update YAML file if any records were deleted
        if deleted_record_ids:
            if click.confirm(
                "Do you want to update the YAML file to remove these records?",
                default=True,
            ):
                # Remove the deleted records from the zone
                zone.records = [r for r in zone.records if r.id not in deleted_record_ids]

                # Save the updated zone
                file_path = yaml_handler.write_zone(zone)
                console.print(f"[green]Updated YAML file:[/] {file_path}")
            elif deleted_record_ids:
                console.print(
                    f"\n[yellow]Please update the YAML file to remove deleted records:[/] {ZONES_DIR / f'{domain}.yaml'}"
                )

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


@cli.command("update")
@click.argument("domain", required=False)
@click.option("--all", is_flag=True, help="Update all zones")
@click.pass_context
def update_zones(ctx: click.Context, domain: Optional[str], all: bool) -> None:
    """
    Check and update DNS records.

    Specify a domain name to update a single zone, or use --all to update all zones.
    """
    yaml_handler = YAMLHandler()
    client = ctx.obj["client"]

    try:
        if all:
            # Update all zones
            for file_path in ZONES_DIR.glob("*.yaml"):
                domain_name = file_path.stem
                zone = yaml_handler.read_zone(domain_name)
                if zone:
                    process_zone_update(zone, yaml_handler, client)

        elif domain:
            # Update specific zone
            zone = yaml_handler.read_zone(domain)

            if not zone:
                console.print(f"[bold red]Error:[/] Domain '{domain}' not found in local database.")
                sys.exit(1)

            process_zone_update(zone, yaml_handler, client)

        else:
            console.print("[bold yellow]Please specify a domain or use --all flag.[/]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        sys.exit(1)


def process_zone_update(zone: Zone, yaml_handler: YAMLHandler, client: HetznerDNSClient) -> bool:
    """
    Update zone records in Hetzner DNS API based on local YAML configuration.

    Args:
        zone: Zone object containing desired record state
        yaml_handler: YAMLHandler instance for file operations
        client: HetznerDNSClient instance for API communication

    Returns:
        True on updated zone, False on no update required
    """
    check_result = check_zone_records(zone, verbose=False)
    missing_records = check_result["missing_records"]
    mismatch_records = check_result["mismatch_records"]

    # If no missing or mismatched records, nothing to do
    if not missing_records and not mismatch_records:
        console.print("[green]All records match. No update needed.[/]")
        return False

    # Handle missing records first
    if missing_records:
        console.print(f"\nFound [bold]{len(missing_records)}[/] missing records:")
        for record in missing_records:
            console.print(f"  - {record.type} {record.name} {record.value}")

        # Ask for confirmation to create missing records
        if click.confirm("Do you want to create the missing records?", default=True):
            create_records = []
            for record in missing_records:
                create_request: RecordCreateRequest = {
                    "zone_id": zone.id,
                    "type": record.type,
                    "name": record.name,
                    "value": record.value,
                }
                create_records.append(create_request)

            # Perform bulk create
            console.print(f"Creating [bold]{len(create_records)}[/] records...")

            result = client.bulk_create_records(create_records)

            # Handle invalid records
            if "invalid_records" in result and result["invalid_records"]:
                console.print("[bold red]Error:[/] Some records failed to create:")
                for record_data in result["invalid_records"]:
                    invalid_record = cast(RecordData, record_data)
                    console.print(f"  - {invalid_record['type']} {invalid_record['name']} {invalid_record['value']}")

            # Handle successfully created records
            if "records" in result and result["records"]:
                console.print(f"[green]Successfully created {len(result['records'])} records.[/]")

                # Ask user to update YAML files to include newly created IDs
                if click.confirm(
                    "Do you want to update the YAML file with the new record IDs?",
                    default=True,
                ):
                    for new_record_data in result["records"]:
                        new_record = cast(RecordData, new_record_data)
                        for record in zone.records:
                            if (
                                record.type == new_record["type"]
                                and record.name == new_record["name"]
                                and record.value == new_record["value"]
                            ):
                                record.id = new_record["id"]

                    # Save the updated zone
                    file_path = yaml_handler.write_zone(zone)
                    console.print(f"[green]Updated YAML file:[/] {file_path}")

    # Handle mismatched records
    if mismatch_records:
        console.print(f"\nFound [bold]{len(mismatch_records)}[/] mismatched records:")
        for record in mismatch_records:
            console.print(f"  - {record.type} {record.name} {record.value}")

        # Ask for confirmation to update mismatched records
        if click.confirm("Do you want to update the mismatched records?", default=True):
            # Prepare records for bulk update
            update_records = []
            for record in mismatch_records:
                update_request: RecordUpdateRequest = {
                    "id": record.id,
                    "type": record.type,
                    "name": record.name,
                    "value": record.value,
                    "zone_id": zone.id,
                }
                update_records.append(update_request)

            # Perform bulk update
            console.print(f"Updating [bold]{len(update_records)}[/] records...")

            result = client.bulk_update_records(update_records)

            if "failed_records" in result and result["failed_records"]:
                console.print("[bold red]Error:[/] Some records failed to update:")
                for record_data in result["failed_records"]:
                    failed_record = cast(RecordData, record_data)
                    console.print(f"  - {failed_record['type']} {failed_record['name']} {failed_record['value']}")
            else:
                console.print("[green]All records updated successfully.[/]")

    return True


if __name__ == "__main__":
    cli()
