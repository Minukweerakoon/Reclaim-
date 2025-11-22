from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import UserModel
from bson import ObjectId
import hashlib

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print("Registration data received:", data)
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        existing_user = UserModel.find_by_email(request.users, data['email'])
        if existing_user:
            print("User already exists:", data['email'])
            return jsonify({'error': 'User already exists'}), 400
        
        hashed_password = hash_password(data['password'])
        print("Password hashed successfully")
        
        user_data = {
            'username': data.get('username', data['email'].split('@')[0]),
            'email': data['email'],
            'password': hashed_password,
            'role': data.get('role', 'student')
        }
        
        result = UserModel.create_user(request.users, user_data)
        print("User created successfully:", str(result.inserted_id))
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print("Registration error:", str(e))
        return jsonify({'error': 'Registration failed: ' + str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("Login attempt for email:", data.get('email'))
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = UserModel.find_by_email(request.users, data['email'])
        if not user:
            print("User not found:", data['email'])
            return jsonify({'error': 'Invalid credentials'}), 401
        
        hashed_password = hash_password(data['password'])
        print("Stored password:", user.get('password'))
        print("Provided password hash:", hashed_password)
        
        if user['password'] != hashed_password:
            print("Password mismatch")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        print("Login successful for user:", user['username'])
        access_token = create_access_token(
            identity=str(user['_id']),
            additional_claims={'role': user['role']}
        )
        
        return jsonify({
            'access_token': access_token,
            'user_id': str(user['_id']),
            'role': user['role'],
            'username': user['username']
        }), 200
        
    except Exception as e:
        print("Login error:", str(e))
        return jsonify({'error': 'Login failed: ' + str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    try:
        current_user = get_jwt_identity()
        user = UserModel.find_by_id(request.users, current_user)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user_id': str(user['_id']),
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/debug-users', methods=['GET'])
def debug_users():
    try:
        users = list(request.users.find())
        user_list = []
        for user in users:
            user_list.append({
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'password': user['password'],
                'role': user['role']
            })
        return jsonify({'users': user_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500