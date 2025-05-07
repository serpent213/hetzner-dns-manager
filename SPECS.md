# Hetzner DNS Manager

Process the API specs in `dns_api.txt` (sorry about the format, had to copy & paste it manually). It's a pretty typical REST/JSON API.

Ultrathink and write a SINGLE FILE executable Python script `dns-manager` to interact with that API.

Use click, ruamel-yaml and rich.

Use uv/PEP 723 to include dependencies.

API token will be read from environment `HETZNER_DNS_API_TOKEN`.

You can find example results for all zones in `example_zones.json` (API Get All Zones) and for all records of one of these zones in `example_zone_records.json` (API Get All Records).

Local database will be a bunch of YAML files named `./zones/${domain}.yaml`, each including zone metadata and all records of that zone.

Create functions to easily make use of the API functions we need to use. Create other functions as appropriate to minimize duplicate code, for example a general API access function and a "check" function to validate a record via DNS (for "check" and "update" actions). Use your own judgement to achieve a clean, readable, maintainable design.

Create dataclasses for zones and records with reasonable validation for the fields we use, so we can catch invalid YAML files easily.

Follow modern Python (3.12+) best practices, functional design, pattern matching, lean & KISS. No typing or tests.

Create a nice `README.md` and a 0-clause BSD license in `LICENSE`.

## CLI Commands

Global option `--dry` to print the first API request that would be performed and then halt.

All commands shall return proper success or error exit codes.

### import

Accepts a domain name as argument or `--all`.

Fetch all zones (API Get All Zones) and all records for the requested zones (API Get All Records, once or multiple times) and write to YAML files.

Include these fields for the zone: `id`, `name`.

Include these fields for each record: `id`, `type`, `name`, `value`.

Order records alphabetically by: 1. type, 2. name.

### check

Accepts a domain name as argument or `--all`.

Go through all records of the selected zones and perform a DNS request matching the record.

Print a nicely formatted output on the console showing match/mismatch/missing for each record (with some kind of green/red indicator).

### delete

Accepts a domain name and a record name as arguments.

Look up the record in out database and delete it (API Delete Record).

Ask user to update the YAML file to delete it there as well.

### update

Copies the behaviour of the "check" action, but then:

In case of at least one miss, ask user to create the missing records. If confirmed, perform a bulk create (API Bulk Create Records) and report success or failure including failed records if any. If we have at least one success, ask user to update the relevant YAML files to include the newly created ids.

In case of at least one mismatch, ask user to perform an update. If confirmed, perform a bulk update (API Bulk Update Records) and report success or failure including failed records if any.
