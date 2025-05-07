# Hetzner DNS Manager

A command-line tool to interact with the Hetzner DNS API, allowing you to manage DNS zones and records.

## Features

- Import zones and records from the Hetzner DNS API
- Check DNS records against actual DNS entries
- Update mismatched DNS records
- Delete DNS records
- Stores zone data in YAML files for easy version control

## Installation

The script uses PEP 723 for dependency management, so it's self-contained. You'll need Python 3.12 or higher.

```bash
# Clone the repository
git clone https://github.com/yourusername/hetzner-dns-manager.git
cd hetzner-dns-manager

# Make the script executable
chmod +x dns-manager

# Create a symbolic link to make it available system-wide (optional)
sudo ln -s $(pwd)/dns-manager /usr/local/bin/dns-manager
```

### Dependencies

The script automatically manages its dependencies using PEP 723. It requires:

- click
- ruamel.yaml
- rich
- dnspython
- requests

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

Check a specific zone against actual DNS entries:

```bash
./dns-manager check example.com
```

Check all zones:

```bash
./dns-manager check --all
```

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

### Help

Display help information:

```bash
./dns-manager help
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

## License

This project is licensed under the 0-clause BSD License - see the [LICENSE](LICENSE) file for details.