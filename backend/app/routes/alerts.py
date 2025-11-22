from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timezone

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    try:
        current_user = get_jwt_identity()
        user = request.users.find_one({'_id': ObjectId(current_user)})
        
        if user['role'] == 'student':
            # Students see only their alerts
            alerts = list(request.alerts.find({'owner_id': ObjectId(current_user)}))
        else:
            # Security staff see all alerts
            alerts = list(request.alerts.find())
        
        for alert in alerts:
            alert['_id'] = str(alert['_id'])
            alert['device_id'] = str(alert['device_id'])
            alert['owner_id'] = str(alert['owner_id'])
            alert['timestamp'] = alert['timestamp'].isoformat()
        
        return jsonify(alerts), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/alerts/<alert_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alert(alert_id):
    try:
        request.alerts.update_one(
            {'_id': ObjectId(alert_id)},
            {'$set': {'resolved': True, 'resolved_at': datetime.now(timezone.utc)}}
        )
        
        return jsonify({'message': 'Alert resolved successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/blacklist', methods=['POST'])
@jwt_required()
def blacklist_device():
    try:
        data = request.get_json()
        device_id = data['device_id']
        current_user = get_jwt_identity()
        
        # Verify user is security staff
        user = request.users.find_one({'_id': ObjectId(current_user)})
        if user['role'] != 'security':
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Add device to blacklist
        request.devices.update_one(
            {'_id': ObjectId(device_id)},
            {'$set': {'is_blacklisted': True, 'status': 'stolen'}}
        )
        
        return jsonify({'message': 'Device blacklisted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500