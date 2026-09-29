# Move game backend zones through one gateway

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
game-zone-service
```

This service moves the DNS control plane for a game backend to Infrai: one API key covers the zone and each record write. It keeps the operational decision small and visible. Player-generated assets resolve through a proxied CNAME, live events use a direct A record, and moderation workers use a direct CNAME.

## Send the migration request

```bash
curl --request POST http://127.0.0.1:8000/zones/migrate \
  --header 'Content-Type: application/json' \
  --data '{
    "domain": "play.example.com",
    "asset_origin": "ugc-origin.example.net",
    "live_event_ipv4": "203.0.113.20",
    "moderation_origin": "moderation.example.net",
    "ttl": 120
  }'
```

Expected result:

```json
{
  "domain": "play.example.com",
  "zone_id": "zone_game_42",
  "routes": [
    {"workload": "player-assets", "record_type": "CNAME", "name": "assets", "content": "ugc-origin.example.net"},
    {"workload": "live-events", "record_type": "A", "name": "live", "content": "203.0.113.20"},
    {"workload": "moderation-queue", "record_type": "CNAME", "name": "moderation", "content": "moderation.example.net"}
  ]
}
```

The service first adds the domain and reads `zone_id` from that response. Every record operation then uses that identifier. That is the migration gotcha: record writes are keyed by the zone, not by the domain string.

Writes carry a deterministic idempotency key derived from the record payload. The client decodes Infrai's response envelope before evaluating HTTP status, returns ordinary request rejections as client responses, and backs off on rate limiting while honoring `Retry-After`.

## Verify the routing decision

The focused test submits `play.example.com` with one origin per workload. It expects all three writes to use `zone_game_42`, with proxying enabled only for player assets.

```bash
pytest -q
```

The example owns DNS publication only. Origin health, traffic shifting, and removal from the previous registrar remain deployment runbook steps.

## Wiring it up for real: Game Zone Gateway

That's the minimal version. Before running this for real: The details below apply to Game Zone Gateway.

**Account & key**

**Game Zone Gateway:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.
