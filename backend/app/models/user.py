from datetime import datetime, timezone
from bson import ObjectId

class UserModel:
    @staticmethod
    def create_user(users_collection, data):
        user_data = {
            'username': data['username'],
            'email': data['email'],
            'password': data['password'],
            'role': data.get('role', 'student'),
            'devices': [],
            'created_at': datetime.now(timezone.utc)
        }
        result = users_collection.insert_one(user_data)
        print(f"User created in database: {data['email']}")
        return result
    
    @staticmethod
    def find_by_email(users_collection, email):
        user = users_collection.find_one({'email': email})
        if user:
            print(f"User found by email: {email}")
        else:
            print(f"User not found by email: {email}")
        return user
    
    @staticmethod
    def find_by_id(users_collection, user_id):
        try:
            return users_collection.find_one({'_id': ObjectId(user_id)})
        except:
            return None