# TLS Setup

## Domain

app.team1.test

## HTTPS Configuration

Nginx is configured to listen on HTTPS port 443.

The TLS certificate is configured in nginx.conf for:

app.team1.test

## Certificate Files

The certificate and private key are stored locally on the Nginx machine.

The private key is NOT included in the GitHub repository.

## Verification

HTTPS was tested using:

curl -i https://app.team1.test/

The response returned:

HTTP/1.1 200 OK

The response also contains:

X-Backend: A

or:

X-Backend: B

This confirms that HTTPS is successfully terminating at Nginx and requests are being forwarded to the backend servers.
