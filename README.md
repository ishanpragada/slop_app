# Slop - Full Stack Application

A full-stack application with React Native + Expo frontend and Python FastAPI backend.

## Project Structure

```
slop/
├── frontend/                 # React Native + Expo app
│   ├── app/                 # Expo Router pages
│   ├── components/          # Reusable components
│   ├── constants/           # App constants
│   ├── hooks/              # Custom hooks
│   ├── assets/             # Images, fonts, etc.
│   ├── package.json
│   ├── app.json
│   └── tsconfig.json
├── backend/                 # Python FastAPI server
│   ├── app/
│   │   ├── main.py         # FastAPI application
│   │   ├── models/         # Database models
│   │   ├── routers/        # API routes
│   │   ├── services/       # Business logic
│   │   └── database/       # Database configuration
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
├── package.json            # Root workspace config
├── docker-compose.yml      # Docker services
└── README.md
```

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- Python 3.11+
- npm or yarn
- Expo CLI (`npm install -g @expo/cli`)

### Installation

1. **Install all dependencies:**
   ```bash
   npm run install:all
   ```

   Or install individually:
   ```bash
   # Frontend dependencies
   npm run frontend:install
   
   # Backend dependencies
   npm run backend:install
   ```

### Development

**Start both frontend and backend:**
```bash
npm run dev
```

**Or start individually:**

Frontend (React Native + Expo):
```bash
npm run frontend:dev
```

Backend (FastAPI):
```bash
npm run backend:dev
```

### API Integration

The FastAPI backend runs on `http://localhost:8000`

Example API call from React Native:
```typescript
const API_BASE_URL = 'http://localhost:8000/api/v1';

const fetchData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/hello`);
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error('API call failed:', error);
  }
};
```

### Docker Deployment

```bash
docker-compose up --build
```

## API Documentation

When the backend is running, visit:
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Project Scripts

- `npm run dev` - Start both frontend and backend
- `npm run frontend:dev` - Start only frontend
- `npm run backend:dev` - Start only backend
- `npm run install:all` - Install all dependencies
- `npm run frontend:install` - Install frontend dependencies
- `npm run backend:install` - Install backend dependencies

## Environment Variables

Backend environment variables (in `backend/.env`):
- AWS credentials for S3 access (configured via aws configure or environment variables)
