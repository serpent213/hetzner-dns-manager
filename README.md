# Hetzner DNS Manager

A command-line tool to interact with the [Hetzner Cloud DNS API](https://docs.hetzner.cloud/reference/cloud#tag/zones), allowing you to manage DNS records by editing a set of YAML files.

It is designed for small to medium installations with up to 100 zones. Function scope is limited to managing records within existing zones for now.

## Features

- Import zones and records from the Hetzner Cloud DNS API
- Check DNS records against actual DNS entries
- Create missing and update mismatched DNS records
- Delete DNS records
- Stores zone data in YAML files for easy manual editing

## Example Workflow

After initial import, add records to an RRSet in a zone YAML file:

![Adding records to a zone YAML file](https://raw.githubusercontent.com/serpent213/hetzner-dns-manager/refs/tags/v0.2.0/docs/demo_edit_add.webp)

Then run *update* to push the change to the API:

![Running the update command](https://raw.githubusercontent.com/serpent213/hetzner-dns-manager/refs/tags/v0.2.0/docs/demo_update.webp)

The same way you can update records and push those.

## Installation

The script uses [PEP 723](https://thisdavej.com/share-python-scripts-like-a-pro-uv-and-pep-723-for-easy-deployment/) for dependency management, so it's self-contained. You'll need Python 3.10 or higher and a working installation of [`uv`](https://docs.astral.sh/uv/), installed via your OS's package manager or via `pip`.

```bash
# Clone the repository
git clone https://github.com/serpent213/hetzner-dns-manager.git
cd hetzner-dns-manager
```

or

```bash
# Download raw script directly
curl -LO https://github.com/serpent213/hetzner-dns-manager/raw/refs/heads/master/hdem
chmod +x hdem
```

### Install from PyPI

Alternatively install from [PyPI](https://pypi.org/project/hetzner-dns-manager/):

```bash
# Install using pip
pip install hetzner-dns-manager

# Or with pipx for isolated installation
pipx install hetzner-dns-manager
```

After installation, you'll have access to the `hdem` command in your terminal.

## Configuration

Set your Hetzner Cloud API token as an environment variable:

```bash
export HCLOUD_TOKEN="your_api_token_here"
```

You may want to add this to your shell profile file (`.bashrc`, `.zshrc`, etc.) for persistence.

By default, hdem reads and writes zone files in `./zones`. Use `--zones-dir` or `HDEM_ZONES_DIR`
to select a different inventory:

```bash
hdem --zones-dir ./live-zones check --all
export HDEM_ZONES_DIR="$HOME/infrastructure/dns"
```

## Usage

The database consists of one YAML file per zone in the configured zones directory.

### Import Zones and Records

Import a specific zone:

```bash
hdem import example.com
```

Import all zones:

```bash
hdem import --all
```

This will create YAML files in the configured zones directory.

Segmented TXT records (like "abc" "def") will be concatenated (to "abcdef") by default. This might be undesirable and can be disabled by passing `--no-txt-concat`.

### Check DNS Records

Check a specific zone against actual DNS entries using one of the domain's authoritative servers:

```bash
hdem check --verbose example.com
```

Check all zones:

```bash
hdem check --all
```

SOA records will be ignored as they are updated automatically by Hetzner.

### Update DNS Records

Check and update mismatched records for a specific zone:

```bash
hdem update example.com
```

Check and update mismatched records for all zones:

```bash
hdem update --all
```

To create new records, add them to the relevant RRSet in your zone YAML. To create a new name/type pair, add a new RRSet.

### Delete DNS Records

Delete a specific record by name:

```bash
hdem delete example.com www
```

If there is more than one candidate, hdem will ask you which records to delete.

### Migrate Local YAML Files

Rewrite a legacy flat `records:` file into the native RRSet format:

```bash
hdem migrate example.com
```

Rewrite all local zone files:

```bash
hdem migrate --all
```

## Data Structure

The YAML files in the configured zones directory follow this RRSet-based structure:

```yaml
version: 2
id: 123456
name: example.com
ttl: 86400
rrsets:
  - name: www
    type: A
    records:
      - value: 192.0.2.1
  - name: '@'
    type: MX
    records:
      - value: '10 mail.example.com.'
```

Older flat `records:` files are still accepted when reading. Normal writes preserve the file format that was read. Use `hdem migrate example.com` or `hdem migrate --all` to rewrite local files in the RRSet format.

## Related Projects

Some other tools dealing with Hetzner DNS (that are not dynamic DNS updaters):

- [hetzner-dns-tools: A simple Hetzner DNS API client for Python and Bash](https://github.com/arcanemachine/hetzner-dns-tools)
- [hdns_cli: Hetzner DNS CLI Tool](https://github.com/lanbugs/hdns_cli/)
