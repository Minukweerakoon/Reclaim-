# Setup Guide for MERN Stack Project

## Prerequisites
- Node.js (v18 or higher)
- npm or yarn
- MongoDB (local or MongoDB Atlas)

## Initial Setup

### 1. Backend Setup

```bash
cd backend
npm install
```

Create a `.env` file in the `backend` directory:
```env
PORT=5000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/reclaim
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRE=7d
CORS_ORIGIN=http://localhost:3000
```

To run the backend:
```bash
npm run dev  # Development mode with nodemon
# or
npm start    # Production mode
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create a `.env` file in the `frontend` directory:
```env
VITE_API_URL=http://localhost:5000/api
VITE_APP_NAME=Reclaim
```

To run the frontend:
```bash
npm run dev    # Development server
npm run build  # Production build
npm run preview # Preview production build
```

## Development Workflow

1. **Start MongoDB**: Make sure MongoDB is running locally or use MongoDB Atlas
2. **Start Backend**: Run `npm run dev` in the `backend` directory
3. **Start Frontend**: Run `npm run dev` in the `frontend` directory
4. **Access Application**: 
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## Project Structure Overview

- **Backend**: Express.js server with MongoDB
- **Frontend**: React application with Vite
- **Separation**: Complete separation of concerns between frontend and backend

## Next Steps

1. Set up MongoDB connection in `backend/src/config/database.js`
2. Create your first model in `backend/src/models/`
3. Create your first route in `backend/src/routes/`
4. Create your first component in `frontend/src/components/`
5. Set up React Router for navigation
6. Implement authentication flow

## Useful Commands

### Backend
- `npm run dev` - Start development server with auto-reload
- `npm start` - Start production server
- `npm test` - Run tests

### Frontend
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests

