# Backend Launch Instructions

The backends are deliberately tiny (Python standard library only, no dependencies): the network is the project.

| | Backend A | Backend B |
|---|---|---|
| Machine | Mac 3 - **10.7.28.30** | Mac 4 - **10.7.10.160** |
| Port | **3001** | **3002** |
| Start | `cd Backend/backend-a && python3 app.py` | `cd Backend/backend-b && python3 app.py` |
| Binds to | `0.0.0.0` (all LAN interfaces - **not** 127.0.0.1) | `0.0.0.0` |
| Identifier header | `X-Backend: A` | `X-Backend: B` |

Endpoints (both): `GET /` -> `{"backend": "A|B", "status": "running"}` and
`GET /api/status` -> `{"backend": "A|B", "status": "ok"}`. Both send `Cache-Control: max-age=30`.

> IP addresses are DHCP-assigned on the shared Wi-Fi and **changed between Phase 1 and Phase 2**
> (Phase 1: 10.7.24.219 / 10.7.18.226 / 10.7.23.31 / 10.7.23.5). Check yours with `ipconfig getifaddr en0` and update
> `dnsmasq.conf` and the `upstream` block of `nginx.conf` if they move again.

## Direct tests

```bash
# from the EDGE Mac (allowed by pf):
curl -i http://10.7.28.30:3001/api/status        # X-Backend: A
curl -i http://10.7.10.160:3002/api/status       # X-Backend: B

# from any OTHER Mac (blocked by pf since Extension C) -> times out:
curl --connect-timeout 5 -i http://10.7.28.30:3001/api/status
```

## Through the edge (what clients must use)

```bash
curl -i https://app.team1.test/api/status
for i in {1..6}; do curl -s -i https://app.team1.test/api/status | grep -E 'HTTP/|X-Backend'; done
```

## Stop / start a backend (failover demo, Extension D)

```bash
# Backend A: press Ctrl-C in its terminal   (or: pkill -f "backend-a/app.py")
# Backend A again:
cd Backend/backend-a && python3 app.py
```
