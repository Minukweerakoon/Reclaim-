# MERN Stack Project Structure

## Overview
This project follows a monorepo structure with separate frontend and backend directories for a MERN (MongoDB, Express, React, Node.js) stack application.

## Folder Structure

```
Reclaim/
├── backend/                    # Node.js/Express Backend
│   ├── src/
│   │   ├── config/            # Configuration files (database, env, etc.)
│   │   ├── controllers/       # Route controllers (business logic)
│   │   ├── models/            # Database models (Mongoose schemas)
│   │   ├── routes/            # API routes
│   │   ├── middleware/        # Custom middleware (auth, validation, etc.)
│   │   ├── utils/             # Utility functions and helpers
│   │   ├── services/          # Business logic services
│   │   ├── validators/        # Input validation schemas
│   │   └── app.js             # Express app setup
│   ├── tests/                 # Backend tests
│   ├── .env.example           # Environment variables template
│   ├── .gitignore
│   ├── package.json
│   └── server.js              # Server entry point
│
├── frontend/                   # React Frontend
│   ├── public/                # Static files
│   │   ├── index.html
│   │   └── assets/            # Images, icons, etc.
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   ├── common/        # Common UI components (Button, Input, etc.)
│   │   │   └── features/      # Feature-specific components
│   │   ├── pages/             # Page components (routes)
│   │   ├── hooks/             # Custom React hooks
│   │   ├── context/           # React Context providers
│   │   ├── services/          # API service functions
│   │   ├── utils/             # Utility functions
│   │   ├── constants/         # Constants and configuration
│   │   ├── styles/            # Global styles, themes
│   │   ├── App.js             # Main App component
│   │   ├── App.css
│   │   └── index.js           # React entry point
│   ├── tests/                 # Frontend tests
│   ├── .env.example           # Environment variables template
│   ├── .gitignore
│   ├── package.json
│   └── README.md
│
├── .gitignore                  # Root gitignore
├── README.md                   # Project documentation
└── PROJECT_STRUCTURE.md        # This file
```

## Backend Structure Details

### `/backend/src/`
- **config/**: Database connections, environment configurations
- **controllers/**: Handle HTTP requests, call services, return responses
- **models/**: Mongoose schemas and models
- **routes/**: API endpoint definitions
- **middleware/**: Authentication, error handling, logging, etc.
- **utils/**: Helper functions (date formatting, string manipulation, etc.)
- **services/**: Business logic layer (separate from controllers)
- **validators/**: Input validation using libraries like Joi or express-validator

### Entry Points
- **server.js**: Starts the Express server
- **app.js**: Configures Express app (middleware, routes, etc.)

## Frontend Structure Details

### `/frontend/src/`
- **components/**: Reusable UI components
  - **common/**: Generic components (Button, Modal, Card, etc.)
  - **features/**: Feature-specific components (LostItemCard, FoundItemForm, etc.)
- **pages/**: Full page components corresponding to routes
- **hooks/**: Custom React hooks for reusable logic
- **context/**: React Context for global state (AuthContext, ThemeContext, etc.)
- **services/**: API calls to backend (axios/fetch wrappers)
- **utils/**: Helper functions (formatters, validators, etc.)
- **constants/**: App-wide constants (API endpoints, status codes, etc.)
- **styles/**: Global CSS, theme files, styled-components

## Best Practices

1. **Separation of Concerns**: Backend handles API logic, frontend handles UI
2. **Environment Variables**: Use `.env` files for configuration (never commit `.env`)
3. **Version Control**: Each folder has its own `package.json` for dependency management
4. **Testing**: Separate test folders for frontend and backend
5. **Scalability**: Structure allows easy addition of new features

## Development Workflow

1. **Backend Development**: Work in `/backend/` directory
2. **Frontend Development**: Work in `/frontend/` directory
3. **Running Both**: Use separate terminals or a process manager like `concurrently`

## Next Steps

1. Initialize backend with `npm init` in `/backend/`
2. Initialize frontend with `create-react-app` or Vite in `/frontend/`
3. Set up MongoDB connection in backend
4. Configure API endpoints
5. Set up React Router for frontend routing
6. Implement authentication flow
7. Connect frontend to backend APIs

