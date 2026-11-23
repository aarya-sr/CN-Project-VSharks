# Phase 2 Runbook - Harden, Recover, Troubleshoot

Everything needed to **repeat** each Phase 2 extension. Commands are the ones used in `Evidence_P2/`.

## Machine inventory (Phase 2)

| Mac | Owner | IP | Roles | Ports |
|---|---|---|---|---|
| Mac 1 | Aarya | 10.7.18.185 | Primary DNS (dnsmasq) | 53/udp+tcp |
| Mac 2 | Suhaani | 10.7.31.36 | Edge: nginx reverse proxy, TLS, load balancer, test client | 443, 8080 |
| Mac 3 | Krishna | 10.7.28.30 | Backend A (+ pf) | 3001 |
| Mac 4 | Vriha | 10.7.10.160 | Backend B (+ pf), **backup DNS**, **standby edge** | 3002, 53, 443 |

Subnet: 10.7.0.0/19 (mask 255.255.224.0). Domain: `team1.test` (never `.local`).

---

## Extension A - Backup DNS resolver

```bash
# Mac 4 (backup): install config = Configuration/phase2/dnsmasq-backup.conf, then
sudo /opt/homebrew/sbin/dnsmasq --test --conf-file=/opt/homebrew/etc/dnsmasq.conf   # "syntax check OK"
sudo brew services start dnsmasq
sudo lsof -nP -iUDP:53 -iTCP:53                                # dnsmasq listening
dig +short @10.7.10.160 app.team1.test api.team1.test         # 10.7.31.36 twice

# Client Mac: list BOTH resolvers (order = priority)
sudo networksetup -setdnsservers Wi-Fi 10.7.18.185 10.7.10.160
networksetup -getdnsservers Wi-Fi

# Failure test: stop the PRIMARY (Mac 1)
sudo brew services stop dnsmasq
sudo lsof -nP -iUDP:53 -iTCP:53                                # nothing listening any more

# Client: names still resolve
dig +time=5 +tries=2 @10.7.10.160 app.team1.test
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
dscacheutil -q host -a name app.team1.test                     # 10.7.31.36 via the OS resolver
```
Restore: `sudo brew services start dnsmasq` on Mac 1.

**DNS-service failure vs application failure.** If both DNS servers are down, *names stop resolving* (`dig` times out /
`could not resolve host`) while IP connectivity still works. If a backend dies, *resolution still works* but the service
answers 502/503 or refuses the connection.

---

## Extension B - DNS TTL and controlled record change

```bash
# Mac 1 (primary) and Mac 4 (backup): host-record=ttl.team1.test,10.7.28.30,30   -> restart dnsmasq
dig @10.7.18.185 ttl.team1.test                 # ANSWER ... 30 IN A 10.7.28.30   (TTL = 30)

# Client Mac: a local caching resolver on 127.0.0.1:5353 forwarding to 10.7.18.185
dig +noall +answer @127.0.0.1 -p 5353 ttl.team1.test      # 30 -> counts down (9, 10 ...) while cached

# Mac 1: change the record to the new IP and restart dnsmasq
host-record=ttl.team1.test,10.7.10.160,30
dig +noall +answer @10.7.18.185 ttl.team1.test           # new IP on the server immediately

# Client: still the OLD IP until the cached TTL runs out, then the NEW IP
dig +noall +answer @127.0.0.1 -p 5353 ttl.team1.test

# Manual flush -> immediate change
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```
Relation to production: lower the TTL *before* a planned migration, change the record, wait one TTL, raise it again.

---

## Extension C - Service isolation with pf

```bash
# 1. Rollback copy FIRST
sudo pfctl -sr    > ~/pf-rollback-rules-$(date +%F).txt
sudo pfctl -si | head -3 > ~/pf-rollback-state-$(date +%F).txt     # records whether pf was enabled
sudo cp /etc/pf.conf ~/pf.conf.backup

# 2. Load the team rules into the anchor (Mac 3: pf-backend-a.rules, Mac 4: pf-backend-b.rules)
sudo pfctl -a 'com.apple/team1' -f ~/pf-team1.rules
sudo pfctl -e                                         # enable pf (harmless if already enabled)
sudo pfctl -a 'com.apple/team1' -sr                   # show the active rules
sudo pfctl -s info | head -5                          # Status: Enabled

# 3. Prove it
curl -i http://10.7.28.30:3001/api/status                         # from the EDGE  -> 200 + X-Backend: A
curl --connect-timeout 5 -i http://10.7.28.30:3001/api/status     # from a CLIENT  -> "Timeout was reached"
curl -i http://10.7.10.160:3002/api/status                        # from the EDGE  -> 200 + X-Backend: B
curl --connect-timeout 5 -i http://10.7.10.160:3002/api/status    # from a CLIENT  -> timeout
curl -s https://app.team1.test/api/status          # via the edge it still works: the EDGE talks to the backend, not the client

# 4. ROLLBACK after the demonstration
sudo pfctl -a 'com.apple/team1' -F rules              # remove the team rules
sudo pfctl -d                                         # only if pf was disabled before (see pf-rollback-state)
```
A silent **timeout** (not "connection refused") is the signature of a `block drop` rule: the packet never reaches the socket.

---

## Extension D - High-availability failover

```bash
# healthy: alternating A / B
for i in {1..5}; do curl -s --max-time 5 -i https://app.team1.test/api/status | grep -E 'HTTP|X-Backend'; done

# Mac 3: stop Backend A (Ctrl-C) -> every response comes from B, none fail
for i in {1..5}; do curl -s --connect-timeout 3 --max-time 5 -i https://app.team1.test/api/status | grep -E 'HTTP|X-Backend'; done

# Mac 3: start Backend A again -> A and B alternate again
for i in {1..6}; do curl -s --connect-timeout 3 --max-time 5 -i https://app.team1.test/api/status | grep -E 'HTTP|X-Backend'; done
```
**Single point of failure:** the edge nginx on Mac 2 (and, below it, the shared Wi-Fi). Removing it needs two edges that
share one virtual IP (VRRP/keepalived) or DNS/anycast health-checked failover - Extension E is the manual version of this.

---

## Extension E - Controlled edge migration (DNS cutover)

```bash
# 0. Standby edge on Mac 4: nginx-standby.conf + the same certificate; check it locally
curl -i --connect-timeout 5 --max-time 10 --resolve app.team1.test:443:127.0.0.1 https://app.team1.test/api/status
# 1. Backends must accept the standby edge: add 10.7.10.160 to the pf allow-list on Mac 3 (pf-backend-a.rules)
# 2. Change app/api records on Mac 1 AND Mac 4 to 10.7.10.160 (commented lines in the dnsmasq files); restart dnsmasq
# 3. Client: verify the cutover
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
dig +short app.team1.test                              # 10.7.10.160
curl -i https://app.team1.test/api/status              # Server: nginx, X-Backend: A|B, no certificate warning
```
Clients that cached the old answer keep using the old edge until the TTL expires (see Extension B). **Rollback:** point the
records back to 10.7.31.36, restart dnsmasq, flush the client cache.

---

## Extension F - Faculty-injected fault

See `Reports/Evaluation_Prep.md` for the layer-by-layer playbook.

---

## Before the demo - make sure the repo matches the live machines

```bash
diff -u /opt/homebrew/etc/dnsmasq.conf  Configuration/phase2/dnsmasq-primary.conf    # Mac 1
diff -u /opt/homebrew/etc/dnsmasq.conf  Configuration/phase2/dnsmasq-backup.conf     # Mac 4
diff -u /opt/homebrew/etc/nginx/nginx.conf Configuration/phase2/nginx-edge.conf      # Mac 2
sudo pfctl -a 'com.apple/team1' -sr                                                  # Mac 3 / Mac 4
```
