from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import click

from hdem import RRSet, Record, Zone, process_zone_update


def make_remote_rrset(name, record_type, values, ttl=None):
    return SimpleNamespace(
        name=name,
        type=record_type,
        ttl=ttl,
        labels={},
        records=[SimpleNamespace(value=value, comment=None) for value in values],
    )


def make_ctx():
    ctx = MagicMock(spec=click.Context)
    ctx.obj = {"dry": False}
    ctx.exit = MagicMock()
    return ctx


def test_update_offers_remote_only_rrsets_before_remote_writes():
    zone = Zone(
        id="123456",
        name="example.com",
        rrsets=[
            RRSet(
                name="www",
                type="A",
                records=[Record(id="", type="A", name="www", value="192.0.2.1")],
            ),
            RRSet(
                name="api",
                type="A",
                records=[Record(id="", type="A", name="api", value="192.0.2.2")],
            ),
        ],
    )
    remote_zone = object()
    client = MagicMock()
    client.zones.get.return_value = remote_zone
    client.zones.get_rrset_all.return_value = [
        make_remote_rrset("www", "A", ["192.0.2.1"]),
        make_remote_rrset("@", "TXT", ['"remote-only"']),
    ]
    yaml_handler = MagicMock()
    yaml_handler.write_zone.return_value = "/zones/example.com.yaml"
    prompts = []

    def confirm(prompt, default):
        prompts.append((prompt, default))
        return len(prompts) == 1

    with patch("hdem.click.confirm", side_effect=confirm):
        process_zone_update(make_ctx(), zone, yaml_handler, client)

    assert prompts == [
        ("Do you want to add these RRSets to the local YAML file?", False),
        ("Do you want to create the missing RRSets?", True),
    ]
    assert any(rrset.name == "@" and rrset.type == "TXT" for rrset in zone.rrsets)
    yaml_handler.write_zone.assert_called_once_with(zone)
    client.zones.create_rrset.assert_not_called()


def test_update_remote_only_rrsets_can_be_declined_without_writing_yaml():
    zone = Zone(
        id="123456",
        name="example.com",
        rrsets=[
            RRSet(
                name="www",
                type="A",
                records=[Record(id="", type="A", name="www", value="192.0.2.1")],
            )
        ],
    )
    client = MagicMock()
    client.zones.get.return_value = object()
    client.zones.get_rrset_all.return_value = [
        make_remote_rrset("www", "A", ["192.0.2.1"]),
        make_remote_rrset("extra", "CNAME", ["target.example.com."]),
    ]
    yaml_handler = MagicMock()

    with patch("hdem.click.confirm", return_value=False) as confirm:
        result = process_zone_update(make_ctx(), zone, yaml_handler, client)

    assert result is False
    confirm.assert_called_once_with("Do you want to add these RRSets to the local YAML file?", default=False)
    assert [(rrset.name, rrset.type) for rrset in zone.rrsets] == [("www", "A")]
    yaml_handler.write_zone.assert_not_called()
