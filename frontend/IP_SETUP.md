# 📱 IP Address Setup for React Native Development

## Why Do I Need an IP Address?

When developing React Native apps with a local backend:

- **Web version** (browser): `localhost` works fine ✅
- **Mobile app** (phone/simulator): needs your computer's **IP address** ❌

Your phone can't connect to "localhost" because that refers to the phone itself, not your computer.

## 🔄 When Your IP Changes

Your IP address changes when:
- 🏠 You switch WiFi networks
- 🔄 Router assigns a new IP  
- ☕ You work from different locations
- 🖥️ Computer restarts

## 🛠️ Easy Solutions

### Option 1: Auto-Detection (Recommended)
The app tries to auto-detect your IP from Expo's development server.

**This usually works automatically!** 🎉

### Option 2: Find & Update IP Manually

1. **Find your current IP:**
   ```bash
   cd frontend
   npm run find-ip
   ```

2. **Update the config file:**
   Open `frontend/config/api.ts` and change:
   ```typescript
   const MANUAL_IP_OVERRIDE = '192.168.68.106'; // ← Update this
   ```

3. **Restart the app**

### Option 3: Command Line Quick Check
```bash
# Find your IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Test backend connection
curl "http://YOUR_IP:8000/api/v1/redis/health"
```

## 🚀 Backend Setup Reminder

Always start your backend with `--host 0.0.0.0`:

```bash
cd backend
source bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Without `--host 0.0.0.0`**, your backend only accepts `localhost` connections!

## 🐛 Debugging

The app shows debug info at the bottom of the screen (development mode only):
- Current API URL being used
- Platform (web/ios/android)  
- Detected IP address
- Number of videos loaded

## 📝 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Network request failed" | Check IP address in config |
| "Connection refused" | Ensure backend uses `--host 0.0.0.0` |
| "No videos" | Backend/Redis might be down |
| App won't load | Try `npm run find-ip` and update config |

## 🎯 Production Notes

In production, you'd use:
- Real domain names (`api.yourapp.com`)
- Environment variables
- CDN for video delivery
- Proper SSL certificates

This IP setup is only for **local development**! 🚧 