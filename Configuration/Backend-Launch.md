# Backend Launch Instructions

## Backend A

Backend A runs on port 3001.

Navigate to the Backend A project directory:

cd backend-a

Start the server:

python3 app.py

Backend A address:

http://10.7.23.31:3001/

Status endpoint:

http://10.7.23.31:3001/api/status

Test:

curl http://10.7.23.31:3001/api/status


## Backend B

Backend B runs on port 3002.

Navigate to the Backend B project directory:

cd backend-b

Start the server:

python3 app.py

Backend B address:

http://10.7.23.5:3002/

Status endpoint:

http://10.7.23.5:3002/api/status

Test:

curl http://10.7.23.5:3002/api/status


## Reverse Proxy

Nginx listens on HTTPS port 443.

Requests to:

https://app.team1.test/

are forwarded to Backend A or Backend B through the Nginx upstream configuration.
