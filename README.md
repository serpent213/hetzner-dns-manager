# Hetzner DNS Manager

A command-line tool to interact with the Hetzner DNS API, allowing you to manage DNS zones and records.

## Features

- Import zones and records from the Hetzner DNS API
- Check DNS records against actual DNS entries
- Create missing and update mismatched DNS records
- Delete DNS records
- Stores zone data in YAML files for easy manual editing

## Installation

The script uses PEP 723 for dependency management, so it's self-contained. You'll need Python 3.12 or higher and typically a working installation of `uv`.

```bash
# Clone the repository
git clone https://github.com/serpent213/hetzner-dns-manager.git
cd hetzner-dns-manager
```

## Configuration

Set your Hetzner DNS API token as an environment variable:

```bash
export HETZNER_DNS_API_TOKEN="your_api_token_here"
```

You may want to add this to your shell profile file (`.bashrc`, `.zshrc`, etc.) for persistence.

## Usage

### Import Zones and Records

Import a specific zone:

```bash
./dns-manager import example.com
```

Import all zones:

```bash
./dns-manager import --all
```

This will create YAML files in the `./zones` directory.

### Check DNS Records

Check a specific zone against actual DNS entries using one of the domain's authoritative servers:

```bash
./dns-manager check example.com
```

Check all zones:

```bash
./dns-manager check --all
```

SOA records will be ignored as they are updated automatically by Hetzner.

### Update DNS Records

Check and update mismatched records for a specific zone:

```bash
./dns-manager update example.com
```

Check and update mismatched records for all zones:

```bash
./dns-manager update --all
```

### Delete a DNS Record

Delete a specific record:

```bash
./dns-manager delete example.com www
```

## Data Structure

The YAML files in the `./zones` directory follow this structure:

```yaml
id: ZoneID
name: example.com
records:
  - id: RecordID1
    type: A
    name: www
    value: 192.0.2.1
  - id: RecordID2
    type: MX
    name: '@'
    value: '10 mail.example.com.'
```

## Related Projects

Some other tools dealing with the Hetzner DNS API (that are not dynamic DNS updaters):

- [A simple Hetzner DNS API client for Python and Bash](https://github.com/arcanemachine/hetzner-dns-tools)
- [Hetzner DNS CLI Tool](https://github.com/lanbugs/hdns_cli/)
