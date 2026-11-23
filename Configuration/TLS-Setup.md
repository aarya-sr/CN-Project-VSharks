# TLS Setup

| Item | Value |
|---|---|
| Domain | `app.team1.test` (SAN also covers `api.team1.test`) |
| Termination point | nginx edge, port **443** (primary 10.7.31.36, standby 10.7.10.160) |
| Protocols | TLS 1.2 and TLS 1.3 (`ssl_protocols` in `nginx-edge.conf`) |
| Trust | The team's local CA certificate is added to the macOS **System** keychain on every client, so no `-k` / `--insecure` is ever used |
| Private key | Stays on the Mac(s) running nginx under `/opt/homebrew/etc/nginx/certs/` - **never committed to GitHub** |

## 1. Create the CA and the server certificate (reference procedure, run once on the edge Mac)

```bash
mkdir -p /opt/homebrew/etc/nginx/certs && cd /opt/homebrew/etc/nginx/certs

# local CA
openssl genrsa -out team1-ca.key 4096
openssl req -x509 -new -key team1-ca.key -sha256 -days 825 \
        -subj "/CN=Team1 Local CA" -out team1-ca.crt

# server key + CSR + certificate with SAN
openssl genrsa -out app.team1.test.key 2048
openssl req -new -key app.team1.test.key -subj "/CN=app.team1.test" -out app.team1.test.csr
printf "subjectAltName=DNS:app.team1.test,DNS:api.team1.test\nextendedKeyUsage=serverAuth\n" > san.ext
openssl x509 -req -in app.team1.test.csr -CA team1-ca.crt -CAkey team1-ca.key -CAcreateserial \
        -days 365 -sha256 -extfile san.ext -out app.team1.test.crt
```

## 2. Trust the CA on every client Mac

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain team1-ca.crt
```

## 3. Standby edge (Extension E)

The standby nginx serves the **same** certificate, so clients that are cut over by DNS see no warning.
Copy `app.team1.test.crt` and `app.team1.test.key` to `/opt/homebrew/etc/nginx/certs/` on the standby Mac over a
trusted channel (AirDrop / `scp`), then `nginx -t && sudo nginx -s reload`.

## 4. Verification (no certificate bypass)

```bash
curl -i https://app.team1.test/api/status                     # HTTP/1.1 200 OK + X-Backend: A|B
openssl s_client -connect app.team1.test:443 -servername app.team1.test </dev/null \
        | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
openssl s_client -connect app.team1.test:443 -servername app.team1.test -CAfile team1-ca.crt </dev/null | grep "Verify return code"
```

Expected: `Verify return code: 0 (ok)`. The handshake (ClientHello -> ServerHello -> Certificate -> Key Exchange ->
Finished) is captured in `Evidence_P1/` (Wireshark, TLS on tcp/443); after it, HTTP is visible only as
*Application Data* - the payload is encrypted.

## 5. Common faults (useful for Extension F)

| Symptom | Layer | Likely cause |
|---|---|---|
| `certificate verify failed` / browser warning | TLS | CA not in the client trust store, or wrong/expired certificate |
| `hostname mismatch` | TLS | certificate SAN does not contain the name used |
| nginx `cannot load certificate key ... Permission denied` | TLS/host | key file not readable by the nginx user |
| `SSL_ERROR_SYSCALL`, connection reset | TCP/TLS | nginx not listening on 443 or a firewall rule drops it |
