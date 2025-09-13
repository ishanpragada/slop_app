#!/usr/bin/env node

const os = require('os');

function findLocalIP() {
  const interfaces = os.networkInterfaces();
  
  for (const name of Object.keys(interfaces)) {
    for (const interface of interfaces[name]) {
      // Skip over non-IPv4 and internal (i.e. 127.0.0.1) addresses
      if (interface.family === 'IPv4' && !interface.internal) {
        return interface.address;
      }
    }
  }
  
  return 'localhost';
}

const currentIP = findLocalIP();

console.log('\n🔍 Current Network Information:');
console.log('================================');
console.log(`Your local IP: ${currentIP}`);
console.log(`Backend URL: http://${currentIP}:8000/api/v1`);

console.log('\n📝 To update your app:');
console.log('1. Open: frontend/config/api.ts');
console.log(`2. Change MANUAL_IP_OVERRIDE to: '${currentIP}'`);
console.log('3. Restart your React Native app');

console.log('\n🚀 Start backend with:');
console.log('cd backend && source bin/activate');
console.log('uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload');

console.log('\n✅ Test connection:');
console.log(`curl "http://${currentIP}:8000/api/v1/redis/health"`); 