from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from .config import config

cors = CORS()
jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Allow all origins for mobile testing
    cors.init_app(app, origins="*")
    jwt.init_app(app)
    
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()
        db = client.theft_prevention_system
        print("MongoDB connected successfully")
        
        collections = ['users', 'devices', 'alerts', 'location_history']
        for collection in collections:
            if collection not in db.list_collection_names():
                db.create_collection(collection)
                print(f"Collection created: {collection}")
        
        @app.before_request
        def before_request():
            request.users = db.users
            request.devices = db.devices
            request.alerts = db.alerts
            request.location_history = db.location_history
            
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        print("Using in-memory database for demo")
        
        class SimpleDB:
            def __init__(self):
                self.data = {
                    'users': [],
                    'devices': [],
                    'alerts': [],
                    'location_history': []
                }
        
        simple_db = SimpleDB()
        
        @app.before_request
        def before_request():
            class MockCollection:
                def __init__(self, data_list):
                    self.data_list = data_list
                
                def find_one(self, query):
                    if 'email' in query:
                        for item in self.data_list:
                            if item.get('email') == query['email']:
                                return item
                    elif '_id' in query:
                        for item in self.data_list:
                            if str(item.get('_id')) == str(query['_id']):
                                return item
                    return None
                
                def insert_one(self, data):
                    import random
                    data['_id'] = f"mock_{random.randint(1000,9999)}"
                    self.data_list.append(data)
                    return type('Result', (), {'inserted_id': data['_id']})()
                
                def update_one(self, query, update):
                    return None
                
                def find(self, query=None):
                    return self.data_list
            
            request.users = MockCollection(simple_db.data['users'])
            request.devices = MockCollection(simple_db.data['devices'])
            request.alerts = MockCollection(simple_db.data['alerts'])
            request.location_history = MockCollection(simple_db.data['location_history'])
    
    from .routes.auth import auth_bp
    from .routes.devices import devices_bp
    from .routes.alerts import alerts_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(devices_bp, url_prefix='/api')
    app.register_blueprint(alerts_bp, url_prefix='/api')
    
    @app.route('/api/health')
    def health():
        return {'status': 'healthy', 'message': 'Theft Prevention System API is running'}
    
    @app.route('/api/debug-db')
    def debug_db():
        try:
            users_count = request.users.count_documents({}) if hasattr(request.users, 'count_documents') else len(request.users.find())
            return {'users_count': users_count, 'db_status': 'connected'}
        except:
            return {'users_count': 0, 'db_status': 'in_memory'}
    
    return app