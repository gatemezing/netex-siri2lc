# netex-siri2lc

Minimal Python MVP for converting NeTEx and SIRI (ET) XML into Linked Connections JSON-LD.

## What’s Included (MVP)
- `netex2lc`: Parse NeTEx `ServiceJourney` passing times into `lc:Connection` resources.
- `siri2lc`: Parse SIRI-ET `EstimatedVehicleJourney` into real-time `lc:Connection` updates.
- JSON-LD output only.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## NeTEx → Linked Connections

```bash
python -m netex2lc \
  --input path/to/netex.xml \
  --output connections.jsonld
```

## SIRI-ET → Linked Connections

```bash
python -m siri2lc \
  --input path/to/siri-et.xml \
  --service-date 2026-02-05 \
  --output realtime.jsonld
```

## Notes / Limitations
- Only JSON-LD output is supported in this MVP.
- SIRI support is limited to ET (Estimated Timetable).
- Time-only SIRI values require `--service-date`.
- URI templates can be provided via `--uris` (JSON). See the spec for template examples.

## Next Steps
- Add fragmenting and server mode.
- Expand SIRI profiles (VM, SX).
- Improve NeTEx coverage (SiteFrame/ServiceFrame metadata).
