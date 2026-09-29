from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from .infrai_dns import InfraiDnsClient, InfraiError
from .zone_service import GameZoneRequest, GameZoneResult, migrate_game_zone

app = FastAPI(title="Game Zone Gateway", version="0.1.0")


@app.post("/zones/migrate", response_model=GameZoneResult)
async def migrate_zone(request: GameZoneRequest) -> GameZoneResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    dns = InfraiDnsClient(api_key)
    try:
        return await migrate_game_zone(request, dns)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    finally:
        await dns.close()

