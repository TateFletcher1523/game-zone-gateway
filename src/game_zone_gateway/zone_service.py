from __future__ import annotations

from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Any, Protocol

from pydantic import BaseModel, Field


class GameZoneRequest(BaseModel):
    domain: str = Field(min_length=3, examples=["play.example.com"])
    asset_origin: str = Field(min_length=3, examples=["ugc-origin.example.net"])
    live_event_ipv4: IPv4Address
    moderation_origin: str = Field(min_length=3, examples=["moderation.example.net"])
    ttl: int = Field(default=60, ge=30, le=86400)


class PublishedRoute(BaseModel):
    workload: str
    record_type: str
    name: str
    content: str


class GameZoneResult(BaseModel):
    domain: str
    zone_id: str
    routes: list[PublishedRoute]


class DnsGateway(Protocol):
    async def add_domain(self, domain: str) -> dict[str, Any]:
        pass

    async def upsert_record(
        self,
        *,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int,
        proxied: bool,
    ) -> dict[str, Any]:
        pass


@dataclass(frozen=True)
class RouteDecision:
    workload: str
    record_type: str
    name: str
    content: str
    proxied: bool


def plan_routes(request: GameZoneRequest) -> list[RouteDecision]:
    return [
        RouteDecision("player-assets", "CNAME", "assets", request.asset_origin, True),
        RouteDecision("live-events", "A", "live", str(request.live_event_ipv4), False),
        RouteDecision("moderation-queue", "CNAME", "moderation", request.moderation_origin, False),
    ]


async def migrate_game_zone(request: GameZoneRequest, dns: DnsGateway) -> GameZoneResult:
    domain_data = await dns.add_domain(request.domain)
    zone_id = domain_data.get("zone_id")
    if not isinstance(zone_id, str) or not zone_id:
        raise RuntimeError("Domain response did not include zone_id")

    decisions = plan_routes(request)
    for route in decisions:
        await dns.upsert_record(
            zone_id=zone_id,
            record_type=route.record_type,
            name=route.name,
            content=route.content,
            ttl=request.ttl,
            proxied=route.proxied,
        )

    return GameZoneResult(
        domain=request.domain,
        zone_id=zone_id,
        routes=[
            PublishedRoute(
                workload=route.workload,
                record_type=route.record_type,
                name=route.name,
                content=route.content,
            )
            for route in decisions
        ],
    )
