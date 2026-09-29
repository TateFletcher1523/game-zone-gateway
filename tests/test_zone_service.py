import asyncio
from typing import Any

from game_zone_gateway.zone_service import GameZoneRequest, migrate_game_zone


class RecordingDnsGateway:
    def __init__(self) -> None:
        self.domain: str | None = None
        self.writes: list[dict[str, Any]] = []

    async def add_domain(self, domain: str) -> dict[str, Any]:
        self.domain = domain
        return {"zone_id": "zone_game_42"}

    async def upsert_record(self, **record: Any) -> dict[str, Any]:
        self.writes.append(record)
        return {"record_id": f"record_{len(self.writes)}"}


def test_migration_routes_each_game_workload_by_zone_id() -> None:
    dns = RecordingDnsGateway()
    request = GameZoneRequest(
        domain="play.example.com",
        asset_origin="ugc-origin.example.net",
        live_event_ipv4="203.0.113.20",
        moderation_origin="moderation.example.net",
        ttl=120,
    )

    result = asyncio.run(migrate_game_zone(request, dns))

    assert result.zone_id == "zone_game_42"
    assert dns.domain == "play.example.com"
    assert dns.writes == [
        {
            "zone_id": "zone_game_42",
            "record_type": "CNAME",
            "name": "assets",
            "content": "ugc-origin.example.net",
            "ttl": 120,
            "proxied": True,
        },
        {
            "zone_id": "zone_game_42",
            "record_type": "A",
            "name": "live",
            "content": "203.0.113.20",
            "ttl": 120,
            "proxied": False,
        },
        {
            "zone_id": "zone_game_42",
            "record_type": "CNAME",
            "name": "moderation",
            "content": "moderation.example.net",
            "ttl": 120,
            "proxied": False,
        },
    ]
