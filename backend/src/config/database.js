const mongoose = require('mongoose');

const connectDB = async () => {
  try {
    // Check if MONGODB_URI is set
    if (!process.env.MONGODB_URI) {
      console.warn('⚠️  MONGODB_URI not set in .env file');
      console.warn('   Server will start but database features will not work');
      console.warn('   Please set MONGODB_URI in backend/.env');
      return;
    }

    // Fix connection string - URL encode password if it contains special characters
    let mongoUri = process.env.MONGODB_URI.trim();
    
    // Handle password with @ symbol - need to find the LAST @ before the host
    // Pattern: mongodb+srv://username:password@host
    if (mongoUri.startsWith('mongodb+srv://')) {
      // Find the protocol part
      const protocol = 'mongodb+srv://';
      const afterProtocol = mongoUri.substring(protocol.length);
      
      // Find username (before first :)
      const colonIndex = afterProtocol.indexOf(':');
      if (colonIndex === -1) {
        throw new Error('Invalid MongoDB URI: missing password');
      }
      
      const username = afterProtocol.substring(0, colonIndex);
      const afterUsername = afterProtocol.substring(colonIndex + 1);
      
      // Find the LAST @ (this separates password from host)
      // Password may contain @, so we need the last one
      const lastAtIndex = afterUsername.lastIndexOf('@');
      if (lastAtIndex === -1) {
        throw new Error('Invalid MongoDB URI: missing host');
      }
      
      const password = afterUsername.substring(0, lastAtIndex);
      const hostAndPath = afterUsername.substring(lastAtIndex + 1);
      
      // URL encode the password (especially @ becomes %40)
      const encodedPassword = encodeURIComponent(password);
      
      // Reconstruct URI
      mongoUri = `${protocol}${username}:${encodedPassword}@${hostAndPath}`;
      
      // Ensure database name is included
      if (!mongoUri.includes('/') || mongoUri.match(/\/[^\/]*$/)) {
        // No database name or ends with just host
        if (mongoUri.endsWith('/')) {
          mongoUri = mongoUri.replace(/\/$/, '') + '/reclaim?retryWrites=true&w=majority';
        } else if (!mongoUri.includes('?')) {
          // Has host but no database or query params
          mongoUri += '/reclaim?retryWrites=true&w=majority';
        }
      } else if (!mongoUri.includes('?')) {
        // Has database but no query params
        mongoUri += '?retryWrites=true&w=majority';
      }
    }

    // Remove deprecated options (not needed in mongoose 8.0+)
    const conn = await mongoose.connect(mongoUri, {
      bufferCommands: true,
      bufferTimeoutMS: 30000
    });

    console.log(`✅ MongoDB Connected: ${conn.connection.host}`);
    console.log(`   Database: ${conn.connection.name}`);
  } catch (error) {
    console.error(`❌ MongoDB Connection Error: ${error.message}`);
    console.error('   Server will continue but database features will not work');
    console.error('   Please check your MONGODB_URI in backend/.env');
    console.error('   Note: If password contains @, it should be URL-encoded as %40');
    console.error('   See backend/QUICK_MONGODB_SETUP.md for setup instructions');
    // Don't exit - allow server to start without database for testing
    // process.exit(1);
  }
};

module.exports = connectDB;

