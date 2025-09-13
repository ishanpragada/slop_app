# Slop Backend

## Quick Start

### Option 1: Using the startup script (Recommended)
```bash
cd backend
./start_server.sh
```

### Option 2: Manual startup
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Important Notes

- **Always use `--host 0.0.0.0`** when starting the server to make it accessible from other devices on your network
- The default `--host localhost` or `--host 127.0.0.1` will only allow connections from the same machine
- Your mobile device needs to connect to your computer's network IP address (e.g., `192.168.68.100:8000`)

## Network Configuration

The backend server needs to be accessible from your mobile device for the app to work properly. 

### Why `--host 0.0.0.0`?
- `localhost` or `127.0.0.1` only allows connections from the same machine
- `0.0.0.0` binds the server to all network interfaces, making it accessible from other devices
- This is necessary for mobile development where your phone and computer are on the same network

### Finding Your IP Address
```bash
ifconfig | grep -E "inet " | grep -v 127.0.0.1 | grep -v 169.254
```

## API Endpoints

- Health Check: `GET /health`
- API Base: `/api/v1`
- Feed: `/api/v1/feed/infinite`

## Troubleshooting

### "Network request failed" error
1. Ensure the backend is running with `--host 0.0.0.0`
2. Check that your firewall allows connections on port 8000
3. Verify the IP address in your frontend config matches your computer's network IP

### Connection refused
1. Make sure the backend is actually running
2. Check if port 8000 is already in use: `lsof -i :8000`
3. Restart the backend server 