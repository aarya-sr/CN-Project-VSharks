# CN-Project-VSharks — Computer Networks Project

## Private Network Service Platform — Phase 1

CN-Project-VSharks is a fully local private network service platform developed for the **Computer Networks Course Project**.

The project demonstrates how a client request travels through a local network using:

**Private DNS → TCP → HTTPS/TLS → Nginx Reverse Proxy → Load Balancing → Backend Service**

The complete system runs locally on four macOS laptops connected to the same private Wi-Fi/LAN. No cloud infrastructure is required.

The primary Phase 1 objective is to build the network infrastructure and use tools such as `dig`, `curl`, and Wireshark to prove what happens at each layer of a client request.

---

# 👥 Team & Machine Roles

| Machine | Team Member | Role | IP Address | Service |
|---|---|---|---|---|
| Mac 1 | Aarya | Private DNS Server | `10.7.24.219` | dnsmasq / DNS :53 |
| Mac 2 | Suhaani | Edge / Reverse Proxy / Load Balancer | `10.7.18.226` | nginx / HTTPS :443 |
| Mac 3 | Krishna | Backend Server A | `10.7.23.31` | HTTP :3001 |
| Mac 4 | Vriha | Backend Server B | `10.7.23.5` | HTTP :3002 |

## LAN Configuration

| Property | Value |
|---|---|
| Network | `10.7.0.0/19` |
| Subnet Mask | `255.255.224.0` |
| Gateway | `10.7.0.1` |
| Interface | Wi-Fi |

The machines operate on the same private LAN and communicate using their private IPv4 addresses.

---

# 🏗️ System Architecture

```text
                         Team 1 Private LAN
                            10.7.0.0/19
                                 │
                                 │
                         DNS Query :53/UDP
                                 │
                                 ▼
                  ┌──────────────────────────┐
                  │       AARYA — Mac 1      │
                  │    Private DNS Server    │
                  │       10.7.24.219        │
                  │         dnsmasq          │
                  └─────────────┬────────────┘
                                │
                   app.team1.test
                       → 10.7.18.226
                                │
                                │ HTTPS :443
                                ▼
                  ┌──────────────────────────┐
                  │     SUHAANI — Mac 2      │
                  │    nginx Edge / Load     │
                  │       Balancer           │
                  │       10.7.18.226        │
                  │        HTTPS :443        │
                  └─────────────┬────────────┘
                                │
                       Round-Robin Load
                           Balancing
                         ┌───────┴───────┐
                         │               │
                         ▼               ▼
              ┌─────────────────┐ ┌─────────────────┐
              │ KRISHNA — Mac 3 │ │  VRIHA — Mac 4  │
              │    Backend A    │ │    Backend B    │
              │   10.7.23.31    │ │    10.7.23.5    │
              │   HTTP :3001    │ │   HTTP :3002    │
              │  X-Backend: A   │ │  X-Backend: B   │
              └─────────────────┘ └─────────────────┘
```

The client communicates with the Nginx edge using the private domain name.

The client does not need to know the backend IP addresses. Nginx selects the backend and forwards the request internally.

---

# 🔄 Request Flow

A normal request follows this sequence:

1. The client requests `app.team1.test`.
2. The client sends a DNS query to the team's private DNS server.
3. `dnsmasq` resolves `app.team1.test` to the Nginx edge IP.
4. The client establishes a TCP connection with the Nginx server.
5. HTTPS/TLS is established on port `443`.
6. Nginx terminates TLS and receives the HTTP request.
7. Nginx forwards the request to Backend A or Backend B.
8. The selected backend returns the response.
9. Nginx sends the response back to the client.

```text
Client
   │
   │ DNS Query
   ▼
Aarya / dnsmasq
10.7.24.219:53
   │
   │ app.team1.test → 10.7.18.226
   ▼
Suhaani / nginx
10.7.18.226:443
   │
   ├──────────────► Krishna / Backend A
   │                10.7.23.31:3001
   │
   └──────────────► Vriha / Backend B
                    10.7.23.5:3002
```

This represents the complete protocol path:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
HTTP
 ↓
Reverse Proxy
 ↓
Backend
```

---

# 🌐 Private DNS

The private DNS server runs on **Mac 1** using `dnsmasq`.

The project uses the reserved `.test` namespace as required by the project specification.

The configured records are:

```text
app.team1.test → 10.7.18.226
api.team1.test → 10.7.18.226
```

The DNS server listens on:

```text
10.7.24.219:53
```

Client Macs are configured to use:

```text
10.7.24.219
```

as their DNS resolver.

DNS resolution can be verified using:

```bash
dig app.team1.test
```

Example successful resolution:

```text
app.team1.test → 10.7.18.226
```

The final application is accessed using the hostname rather than directly entering the Nginx IP address.

This demonstrates the difference between **DNS resolution** and the TCP/HTTPS connection that follows the resolution.

---

# 🖥️ Backend Services

The project uses two lightweight local HTTP backend services.

The backend applications are intentionally simple because the project evaluates the network configuration rather than application complexity.

## Backend A

**Host:** Krishna — Mac 3

```text
IP:       10.7.23.31
Port:     3001
Backend:  A
```

The backend provides an application status endpoint:

```text
GET /api/status
```

Example response:

```json
{
  "backend": "A",
  "status": "ok"
}
```

The response identifies the backend using:

```text
X-Backend: A
```

Backend A can also be reached directly on the LAN for testing:

```text
http://10.7.23.31:3001
```

However, clients use the Nginx edge for the final application demonstration.

---

## Backend B

**Host:** Vriha — Mac 4

```text
IP:       10.7.23.5
Port:     3002
Backend:  B
```

The backend provides:

```text
GET /api/status
```

Example response:

```json
{
  "backend": "B",
  "status": "ok"
}
```

The response identifies the backend using:

```text
X-Backend: B
```

Backend B can also be reached directly on the LAN for testing:

```text
http://10.7.23.5:3002
```

---

# ⚖️ Nginx Reverse Proxy & Load Balancing

Nginx runs on **Mac 2** and acts as the single public entry point for the application.

The backend pool contains:

```text
Backend A → 10.7.23.31:3001
Backend B → 10.7.23.5:3002
```

Nginx uses load balancing to distribute requests between the two backend services.

Repeated requests to:

```text
https://app.team1.test/api/status
```

can return:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

The `X-Backend` response header makes the selected backend visible during testing.

This demonstrates that:

- the client communicates with the Nginx edge;
- the client does not select a backend directly;
- Nginx forwards requests to the backend pool;
- multiple backend servers can serve the same application endpoint.

---

# 🔐 HTTPS / TLS

HTTPS is terminated at the Nginx edge server.

```text
Hostname: app.team1.test
Server:   10.7.18.226
Port:     443
Protocol: HTTPS
```

A local certificate authority is used for the project certificate.

The certificate is issued for:

```text
CN = app.team1.test
```

and the local CA is:

```text
Team1 Local CA
```

The certificate verification evidence shows:

```text
Protocol: TLSv1.3
Cipher: TLS_AES_256_GCM_SHA384
Verify return code: 0 (ok)
```

The project also captures the TLS handshake using `curl` and Wireshark.

The TLS exchange includes stages such as:

```text
ClientHello
    ↓
ServerHello
    ↓
Certificate
    ↓
Certificate Verification
    ↓
Finished
    ↓
Encrypted Application Data
```

The HTTPS demonstration is performed without relying on the `-k` certificate-validation bypass.

Example:

```bash
curl -v https://app.team1.test/api/status
```

---

# 💾 HTTP Caching

The backend responses include an HTTP caching header:

```text
Cache-Control: max-age=30
```

The project demonstrates cache behavior using the Nginx/application response headers.

The evidence shows cache states including:

```text
X-Cache-Status: MISS
X-Cache-Status: HIT
X-Cache-Status: EXPIRED
```

This demonstrates the difference between:

- a request that is not currently served from cache;
- a request served from a valid cached response;
- a request after the cache lifetime has expired.

The cache lifetime used in the demonstrated configuration is:

```text
max-age=30
```

---

# 📡 Wireshark Protocol Analysis

Wireshark is used to provide packet-level evidence for the network flow.

The captures cover the major layers required for Phase 1.

## DNS

The DNS capture shows queries for:

```text
app.team1.test
```

and responses resolving the hostname to:

```text
10.7.18.226
```

The DNS service uses:

```text
UDP :53
```

Example flow:

```text
Client
   │
   │ DNS Query
   │ UDP destination port 53
   ▼
10.7.24.219
   │
   │ DNS Response
   ▼
Client
```

---

## TCP

The project captures TCP communication involving the backend services.

The TCP three-way handshake is:

```text
SYN
 ↓
SYN-ACK
 ↓
ACK
```

The evidence includes TCP traffic involving:

```text
Backend A → port 3001
Backend B → port 3002
HTTPS Edge → port 443
```

The client uses an ephemeral source port while the server listens on its service port.

---

## TLS

The Wireshark captures include TLS traffic for:

```text
app.team1.test
```

The HTTPS connection uses:

```text
TCP :443
```

The capture shows the TLS ClientHello and server-side TLS response, followed by encrypted application data.

The encrypted application data demonstrates that the HTTP payload is not transmitted as readable plaintext after TLS is established.

---

## HTTP / Backend Identification

The HTTP response headers identify which backend processed the request:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

This provides application-level evidence for the Nginx load-balancing behavior.

---

# 🧪 Controlled Failure & Troubleshooting Evidence

The evidence folder also contains controlled failure demonstrations and supporting troubleshooting evidence.

These are retained as part of the project evidence set.

## Wrong DNS Server

A client was configured to use:

```text
8.8.8.8
```

instead of the team's private DNS server.

The lookup:

```bash
dig app.team1.test
```

returned:

```text
NXDOMAIN
```

This demonstrates that DNS resolution can fail even when the machines themselves still have network connectivity.

The client was subsequently restored to:

```text
10.7.24.219
```

---

## DNS Cache Flush / Recovery

The DNS cache was manually flushed using:

```bash
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

The domain was then resolved again through the project DNS server.

This demonstrates the effect of local DNS caching and cache clearing.

---

## Backend Failure

Evidence also shows requests continuing to return:

```text
X-Backend: B
```

when Backend A was unavailable.

This demonstrates continued service through the remaining backend.

---

## Wrong Destination Port

The application was deliberately accessed using an incorrect destination port:

```text
https://app.team1.test:9999/api/status
```

The connection failed because no service was listening on that port.

This demonstrates the distinction between:

```text
IP address
```

and:

```text
TCP destination port
```

---

# 🧰 Technologies Used

- macOS
- Private Wi-Fi / LAN
- dnsmasq
- Nginx
- Python
- OpenSSL
- curl
- dig
- networksetup
- Wireshark
- Git
- GitHub

---

# 📁 Repository Structure

```text
CN-Project-VSharks/
│
├── README.md
│
├── Architecture/
│   └── ...
│
├── Backend/
│   └── ...
│
├── Configuration/
│   └── ...
│
├── Evidence/
│   ├── 01_lan_mac1_dns_server.jpeg
│   ├── 02_lan_mac2_edge_proxy.jpeg
│   ├── 03_lan_mac3_backend_a.jpeg
│   ├── 04_lan_mac4_backend_b.jpeg
│   ├── ...
│   └── 45_dnsmasq_configuration_reference.jpeg
│
├── Presentation/
│   └── ...
│
└── Reports/
    └── ...
```

The Evidence folder contains the complete screenshot evidence collected for the project. Screenshots have been given sequential names so that evidence can be located quickly during evaluation.

---

# 📸 Phase 1 Evidence Index

The evidence is organized according to the seven mandatory Phase 1 tasks.

## Task A — Establish the Private LAN

Relevant evidence includes:

```text
01_lan_mac1_dns_server.jpeg
02_lan_mac2_edge_proxy.jpeg
03_lan_mac3_backend_a.jpeg
04_lan_mac4_backend_b.jpeg

12_ping_mac2_edge.jpeg
13_ping_backend_a_10_7_23_31.jpeg
14_ping_backend_b_10_7_23_5.jpeg
15_ping_backend_a_10_7_23_31_repeat.jpeg
16_ping_multiple_hosts.jpeg
17_ping_dns_server_10_7_24_219.jpeg
18_ping_mac2_from_backend_b.jpeg
```

These demonstrate machine IP configuration and LAN reachability.

---

## Task B — Configure a Private DNS Server

Relevant evidence includes:

```text
05_dnsmasq_record_configuration.jpeg
06_client_dns_server_configuration.jpeg
07_client_dns_server_configuration_duplicate.jpeg
08_client_dns_server_address_verified.jpeg

09_dns_app_and_api_resolution.jpeg
10_dns_app_resolution_short.jpeg
11_dns_app_resolution_detailed.jpeg
```

The DNS server provides:

```text
app.team1.test → 10.7.18.226
api.team1.test → 10.7.18.226
```

---

## Task C — Build Two Simple Backend Services

Relevant evidence includes:

```text
19_backend_b_direct_api_response.jpeg
20_backend_a_running.jpeg
```

Additional backend packet evidence:

```text
30_wireshark_backend_a_tcp_3001.jpeg
31_wireshark_backend_b_tcp_3002.jpeg
```

The backends listen on:

```text
Backend A → 3001
Backend B → 3002
```

---

## Task D — Configure the Edge Reverse Proxy and Load Balancer

Relevant evidence includes:

```text
28_load_balancing_alternating_backends.jpeg
29_load_balancing_alternating_backends_duplicate.jpeg
```

Repeated requests demonstrate the backend selected by Nginx through the:

```text
X-Backend
```

response header.

---

## Task E — Add HTTPS / TLS

Relevant evidence includes:

```text
22_https_application_response.jpeg

24_curl_tls_handshake_and_https_response.jpeg
25_openssl_tls_certificate_verification.jpeg
26_openssl_tls_certificate_verification_duplicate.jpeg
27_browser_certificate_validity.jpeg

34_wireshark_tls_general_capture.jpeg
35_wireshark_tls_general_capture.jpeg
36_wireshark_tcp_443_tls_application_data.jpeg
```

The strongest TLS evidence includes certificate verification and TLSv1.3 negotiation.

---

## Task F — Demonstrate HTTP Caching Behavior

Relevant evidence:

```text
37_http_caching_miss_hit_expired.jpeg
```

The screenshot demonstrates:

```text
Cache-Control: max-age=30
```

and cache states including:

```text
MISS
HIT
EXPIRED
```

---

## Task G — Capture the Complete Protocol Flow

Relevant evidence includes:

### DNS

```text
32_wireshark_project_dns_query_response.jpeg
33_wireshark_dns_general_capture.jpeg
```

### TCP / Backend Ports

```text
30_wireshark_backend_a_tcp_3001.jpeg
31_wireshark_backend_b_tcp_3002.jpeg
```

### TLS / HTTPS

```text
24_curl_tls_handshake_and_https_response.jpeg
34_wireshark_tls_general_capture.jpeg
35_wireshark_tls_general_capture.jpeg
36_wireshark_tcp_443_tls_application_data.jpeg
```

### HTTP / Application

```text
22_https_application_response.jpeg
```

### Load Balancing

```text
28_load_balancing_alternating_backends.jpeg
29_load_balancing_alternating_backends_duplicate.jpeg
```

---

# 📋 Phase 1 Requirement Coverage

| Phase 1 Requirement | Evidence |
|---|---|
| Private LAN connectivity | `01–04`, `12–18` |
| Machine IP configuration | `01–04` |
| Ping / reachability | `12–18` |
| Private DNS server | `05–08` |
| DNS records | `05`, `09–11` |
| DNS resolution | `09–11` |
| Backend A | `20`, `30` |
| Backend B | `19`, `31` |
| Nginx reverse proxy | `22`, `28–29` |
| Load balancing | `28–29` |
| HTTPS | `22`, `24–27` |
| TLS certificate verification | `25–27` |
| TLS packet evidence | `34–36` |
| TCP / service ports | `30–31`, `36` |
| HTTP caching | `37` |
| DNS packet analysis | `32–33` |
| Complete protocol flow | `22`, `28–29`, `30–36` |
| Controlled failure / diagnosis evidence | `38–42` |

---

# ✅ Phase 1 Summary

The Phase 1 implementation demonstrates a complete local private service environment consisting of:

```text
Private LAN
    ↓
Private DNS
    ↓
TCP Connectivity
    ↓
HTTPS / TLS
    ↓
Nginx Reverse Proxy
    ↓
Load Balancing
    ↓
Backend A / Backend B
```

The system was tested using:

```text
ping
dig
curl
networksetup
OpenSSL
Wireshark
```

The evidence demonstrates the network at multiple levels rather than relying only on application output.

The project specifically focuses on understanding how a request travels through the network and how DNS, TCP, TLS, HTTP, caching, and load balancing interact in a complete local service environment.

---

# 🎓 Phase 1 Scope

This repository documents:

**Phase 1 — Build and Observe**

The major networking concepts demonstrated are:

```text
DNS
TCP
UDP
HTTP/REST
HTTPS
TLS
Reverse Proxy
Load Balancing
HTTP Caching
Packet Analysis
Network Troubleshooting
```

Phase 1 is the foundation for the later resilience and recovery extensions of the project.
