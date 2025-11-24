# Reclaim Backend

Node.js/Express backend API for the Reclaim Lost and Found System.

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (copy from `env.example.txt`):
```env
PORT=5000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/reclaim
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRE=7d
CORS_ORIGIN=http://localhost:3000
```

3. Start the development server:
```bash
npm run dev
```

The API will be available at `http://localhost:5000`

## Available Scripts

- `npm start` - Start production server
- `npm run dev` - Start development server with auto-reload (nodemon)
- `npm test` - Run tests

## Project Structure

- `/src/config` - Configuration files (database, etc.)
- `/src/controllers` - Route controllers (business logic)
- `/src/models` - Database models (Mongoose schemas)
- `/src/routes` - API routes
- `/src/middleware` - Custom middleware
- `/src/utils` - Utility functions
- `/src/services` - Business logic services
- `/src/validators` - Input validation schemas

## API Endpoints

- `GET /api/health` - Health check endpoint

