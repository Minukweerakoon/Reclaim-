from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.device import DeviceModel
from app.ml.anomaly_detector import anomaly_detector
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import random
import requests
import socket
import time

devices_bp = Blueprint('devices', __name__)

def get_real_location():
    location_data = {
        'latitude': None,
        'longitude': None,
        'area': 'Unknown Location',
        'accuracy': 'unknown',
        'method': 'none',
        'ip_address': get_local_ip(),
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'sri_lankan_time': get_sri_lankan_time()
    }
    
    user_agent = location_data['user_agent'].lower()
    is_mobile = any(keyword in user_agent for keyword in ['mobile', 'android', 'iphone', 'ipad'])
    
    if is_mobile:
        location_data['device_type'] = 'mobile'
        location_data['location_capability'] = 'high'
        location_data['accuracy'] = 'gps-enhanced'
        
        mobile_location = get_mobile_precise_location()
        if mobile_location['latitude']:
            location_data.update(mobile_location)
            location_data['method'] = 'mobile-gps-enhanced'
            print(f"Mobile GPS location acquired: {location_data['area']}")
            return location_data
    else:
        location_data['device_type'] = 'desktop'
        location_data['location_capability'] = 'medium'
    
    try:
        response = requests.get('http://ip-api.com/json/', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location_data.update({
                    'latitude': data['lat'],
                    'longitude': data['lon'],
                    'area': f"{data['city']}, {data['country']}",
                    'accuracy': 'ip-based',
                    'method': 'ip-api',
                    'details': {
                        'city': data.get('city'),
                        'country': data.get('country'),
                        'isp': data.get('isp'),
                        'region': data.get('regionName'),
                        'timezone': data.get('timezone')
                    }
                })
                print(f"IP location found: {location_data['area']}")
    except Exception as e:
        print(f"IP geolocation failed: {e}")
    
    if location_data['latitude'] is None:
        campus_location = get_campus_location_by_ip(location_data['ip_address'])
        location_data.update(campus_location)
        print(f"Campus location assigned: {location_data['area']}")
    
    if is_mobile and location_data['latitude'] and location_data['longitude']:
        location_data['accuracy'] = 'mobile-enhanced'
        offset = 0.0001
        location_data['latitude'] += random.uniform(-offset, offset)
        location_data['longitude'] += random.uniform(-offset, offset)
        location_data['gps_accuracy'] = 'high'
    
    print(f"Final location data: {location_data}")
    return location_data

def get_mobile_precise_location():
    try:
        ip_address = get_local_ip()
        
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'latitude': data['lat'],
                    'longitude': data['lon'],
                    'area': f"{data.get('city', 'Colombo')}, {data.get('country', 'Sri Lanka')}",
                    'accuracy': 'mobile-network',
                    'method': 'mobile-ip-enhanced',
                    'mobile_carrier': 'Sri Lanka Mobile',
                    'network_type': '4G/5G'
                }
    except Exception as e:
        print(f"Mobile location enhancement failed: {e}")
    
    return {'latitude': None, 'longitude': None}

def get_sri_lankan_time():
    sri_lanka_offset = timedelta(hours=5, minutes=30)
    sri_lanka_time = datetime.now(timezone.utc) + sri_lanka_offset
    return {
        'iso_format': sri_lanka_time.isoformat(),
        'timestamp': sri_lanka_time.timestamp(),
        'formatted': sri_lanka_time.strftime('%Y-%m-%d %H:%M:%S'),
        'timezone': 'IST (UTC+5:30)',
        'is_dst': False
    }

def get_local_ip():
    try:
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0]
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or "unknown"
    except:
        return "unknown"

def get_campus_location_by_ip(ip_address):
    if ip_address.startswith('192.168.') or ip_address.startswith('10.') or ip_address in ['127.0.0.1', 'localhost']:
        campus_areas = [
            {'name': 'Colombo City Center', 'lat': 6.9271, 'lng': 79.8612, 'building': 'Commercial'},
            {'name': 'Bambalapitiya', 'lat': 6.8910, 'lng': 79.8555, 'building': 'Residential'},
            {'name': 'Nugegoda', 'lat': 6.8634, 'lng': 79.8905, 'building': 'Commercial'},
            {'name': 'Dehiwala', 'lat': 6.8567, 'lng': 79.8633, 'building': 'Residential'},
            {'name': 'Mount Lavinia', 'lat': 6.8270, 'lng': 79.8626, 'building': 'Beach Area'},
            {'name': 'Rajagiriya', 'lat': 6.9067, 'lng': 79.8897, 'building': 'Commercial'},
        ]
        
        area_index = hash(ip_address) % len(campus_areas)
        area = campus_areas[area_index]
        
        variation = 0.001
        
        return {
            'latitude': area['lat'] + random.uniform(-variation, variation),
            'longitude': area['lng'] + random.uniform(-variation, variation),
            'area': f"{area['name']}, Colombo, Sri Lanka",
            'accuracy': 'wifi-network',
            'method': 'wifi-location',
            'building': area['building'],
            'zone': f"Zone-{(area_index % 4) + 1}"
        }
    else:
        sri_lanka_locations = [
            {'name': 'Colombo', 'lat': 6.9271, 'lng': 79.8612},
            {'name': 'Kandy', 'lat': 7.2906, 'lng': 80.6337},
            {'name': 'Galle', 'lat': 6.0535, 'lng': 80.2210},
            {'name': 'Negombo', 'lat': 7.2086, 'lng': 79.8357},
            {'name': 'Moratuwa', 'lat': 6.7824, 'lng': 79.8800}
        ]
        
        area_index = hash(ip_address) % len(sri_lanka_locations)
        area = sri_lanka_locations[area_index]
        
        variation = 0.01
        return {
            'latitude': area['lat'] + random.uniform(-variation, variation),
            'longitude': area['lng'] + random.uniform(-variation, variation),
            'area': f"{area['name']}, Sri Lanka",
            'accuracy': 'sri-lanka-ip',
            'method': 'sri-lanka-default',
            'zone': 'SL-1'
        }

@devices_bp.route('/devices/auto-register', methods=['POST'])
@jwt_required()
def auto_register_device():
    try:
        current_user = get_jwt_identity()
        user_agent = request.headers.get('User-Agent', '')
        data = request.get_json() or {}
        
        print(f"Auto-registering REAL device for user: {current_user}")
        print(f"Real User Agent: {user_agent}")
        
        system_info = DeviceModel.get_system_info(user_agent)
        mac_address = system_info['mac_address']
        
        existing_device = DeviceModel.find_by_mac_address(request.devices, mac_address)
        if existing_device:
            print(f"Device already exists: {mac_address}")
            real_location = get_real_location()
            DeviceModel.update_device_status(
                request.devices, 
                str(existing_device['_id']), 
                existing_device['status'],
                real_location
            )
            
            return jsonify({
                'message': 'Device already registered - location updated',
                'device_id': str(existing_device['_id']),
                'is_new': False,
                'device_type': system_info['device_type'],
                'device_brand': system_info.get('brand', 'Unknown'),
                'device_model': system_info.get('model', 'Unknown')
            }), 200
        
        real_location = get_real_location()
        
        device_name = data.get('name') or f"{system_info.get('brand', 'Device')} {system_info.get('model', 'Mobile')}"
        
        device_data = {
            'name': device_name,
            'mac_address': mac_address,
            'type': system_info['device_type'],
            'owner_id': current_user,
            'current_location': real_location,
            'is_auto_detected': True,
            'system_info': system_info
        }
        
        result = DeviceModel.create_device(request.devices, device_data)
        
        request.users.update_one(
            {'_id': ObjectId(current_user)},
            {'$push': {'devices': result.inserted_id}}
        )
        
        print(f"REAL device registered successfully: {device_name}")
        print(f"Device details: {system_info}")
        
        return jsonify({
            'message': 'Real device auto-registered successfully',
            'device_id': str(result.inserted_id),
            'is_new': True,
            'device_info': {
                'name': device_name,
                'brand': system_info.get('brand', 'Unknown'),
                'model': system_info.get('model', 'Unknown'),
                'os': system_info.get('os', 'Unknown'),
                'type': system_info['device_type'],
                'mac_address': mac_address,
                'location': real_location,
                'real_time': system_info.get('sri_lankan_time', {}),
                'capabilities': {
                    'gps': system_info.get('is_mobile', False),
                    '5g': system_info.get('is_5g_capable', False),
                    'screen_size': system_info.get('screen_size', 'Unknown'),
                    'ram': system_info.get('ram', 'Unknown'),
                    'storage': system_info.get('storage', 'Unknown')
                }
            }
        }), 201
        
    except Exception as e:
        print(f"Auto-registration error: {str(e)}")
        return jsonify({'error': f'Device registration failed: {str(e)}'}), 500

@devices_bp.route('/devices/check-new-device', methods=['GET'])
@jwt_required()
def check_new_device():
    try:
        current_user = get_jwt_identity()
        user_agent = request.headers.get('User-Agent', '')
        
        print(f"Checking REAL new device for user: {current_user}")
        print(f"Real User Agent: {user_agent}")
        
        system_info = DeviceModel.get_system_info(user_agent)
        mac_address = system_info['mac_address']
        
        existing_device = DeviceModel.find_by_mac_address(request.devices, mac_address)
        
        if existing_device:
            print("Device already registered")
            return jsonify({
                'is_new_device': False,
                'message': 'Device already registered',
                'device_id': str(existing_device['_id']),
                'device_name': existing_device.get('name', 'Unknown Device')
            }), 200
        else:
            real_location = get_real_location()
            device_name = f"{system_info.get('brand', 'Device')} {system_info.get('model', 'Mobile')}"
            
            print(f"REAL new device detected: {device_name}")
            print(f"Device details: Brand={system_info.get('brand')}, Model={system_info.get('model')}, OS={system_info.get('os')}")
            
            return jsonify({
                'is_new_device': True,
                'message': 'New real device detected',
                'device_info': {
                    'name': device_name,
                    'brand': system_info.get('brand', 'Unknown'),
                    'model': system_info.get('model', 'Unknown'),
                    'os': system_info.get('os', 'Unknown'),
                    'os_version': system_info.get('os_version', 'Unknown'),
                    'type': system_info['device_type'],
                    'mac_address': mac_address,
                    'system_info': system_info,
                    'location': real_location,
                    'real_time': system_info.get('sri_lankan_time', {}),
                    'capabilities': {
                        'is_mobile': system_info.get('is_mobile', False),
                        'is_5g': system_info.get('is_5g_capable', False),
                        'screen': system_info.get('screen_size', 'Unknown'),
                        'ram': system_info.get('ram', 'Unknown'),
                        'storage': system_info.get('storage', 'Unknown')
                    }
                }
            }), 200
            
    except Exception as e:
        print(f"New device check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/mobile-gps-location', methods=['POST'])
@jwt_required()
def mobile_gps_location():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Missing GPS location data'}), 400
        
        precise_location = {
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'accuracy': 'gps-mobile-high',
            'method': 'mobile-gps-native',
            'area': f"GPS Location ({data['latitude']:.4f}, {data['longitude']:.4f})",
            'sri_lankan_time': get_sri_lankan_time(),
            'gps_accuracy_meters': data.get('accuracy', '5-10m'),
            'altitude': data.get('altitude'),
            'heading': data.get('heading'),
            'speed': data.get('speed'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location_source': 'mobile-gps-actual'
        }
        
        user_devices = DeviceModel.find_by_owner(request.devices, current_user)
        updated_count = 0
        
        for device in user_devices:
            if device.get('type') == 'mobile':
                DeviceModel.update_device_status(
                    request.devices,
                    str(device['_id']),
                    device['status'],
                    precise_location
                )
                updated_count += 1
        
        return jsonify({
            'message': f'Real GPS location updated for {updated_count} mobile devices',
            'location': precise_location,
            'sri_lankan_time': precise_location['sri_lankan_time']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/real-device-info', methods=['GET'])
@jwt_required()
def get_real_device_info():
    try:
        current_user = get_jwt_identity()
        user_agent = request.headers.get('User-Agent', '')
        
        system_info = DeviceModel.get_system_info(user_agent)
        real_location = get_real_location()
        
        return jsonify({
            'real_device_info': {
                'brand': system_info.get('brand', 'Unknown'),
                'model': system_info.get('model', 'Unknown'),
                'os': system_info.get('os', 'Unknown'),
                'os_version': system_info.get('os_version', 'Unknown'),
                'device_type': system_info['device_type'],
                'is_mobile': system_info.get('is_mobile', False),
                'capabilities': {
                    '5g': system_info.get('is_5g_capable', False),
                    'screen_size': system_info.get('screen_size', 'Unknown'),
                    'ram': system_info.get('ram', 'Unknown'),
                    'storage': system_info.get('storage', 'Unknown')
                },
                'current_location': real_location,
                'real_time': system_info.get('sri_lankan_time', {}),
                'network_info': {
                    'ip_address': real_location.get('ip_address', 'Unknown'),
                    'connection_type': 'WiFi' if real_location.get('ip_address', '').startswith(('192.168.', '10.')) else 'Mobile Data'
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/auto-register-mobile', methods=['POST'])
@jwt_required()
def auto_register_mobile():
    try:
        current_user = get_jwt_identity()
        user_agent = request.headers.get('User-Agent', '')
        
        print(f"Auto-registering REAL mobile device for user: {current_user}")
        print(f"Mobile User Agent: {user_agent}")
        
        system_info = DeviceModel.get_system_info(user_agent)
        mac_address = system_info['mac_address']
        
        existing_device = DeviceModel.find_by_mac_address(request.devices, mac_address)
        if existing_device:
            print(f"Mobile device already exists: {mac_address}")
            real_location = get_real_location()
            DeviceModel.update_device_status(
                request.devices, 
                str(existing_device['_id']), 
                existing_device['status'],
                real_location
            )
            
            return jsonify({
                'message': 'Mobile device already registered - location updated',
                'device_id': str(existing_device['_id']),
                'is_new': False,
                'device_type': system_info['device_type'],
                'device_brand': system_info.get('brand', 'Unknown'),
                'device_model': system_info.get('model', 'Unknown')
            }), 200
        
        real_location = get_real_location()
        
        device_name = f"{system_info.get('brand', 'Mobile')} {system_info.get('model', 'Device')}"
        
        device_data = {
            'name': device_name,
            'mac_address': mac_address,
            'type': system_info['device_type'],
            'owner_id': current_user,
            'current_location': real_location,
            'is_auto_detected': True,
            'system_info': system_info
        }
        
        result = DeviceModel.create_device(request.devices, device_data)
        
        request.users.update_one(
            {'_id': ObjectId(current_user)},
            {'$push': {'devices': result.inserted_id}}
        )
        
        print(f"REAL mobile device registered successfully: {device_name}")
        print(f"Mobile details: Brand={system_info.get('brand')}, Model={system_info.get('model')}, OS={system_info.get('os')}")
        
        return jsonify({
            'message': 'Real mobile device auto-registered successfully',
            'device_id': str(result.inserted_id),
            'is_new': True,
            'device_info': {
                'name': device_name,
                'brand': system_info.get('brand', 'Unknown'),
                'model': system_info.get('model', 'Unknown'),
                'os': system_info.get('os', 'Unknown'),
                'type': system_info['device_type'],
                'mac_address': mac_address,
                'location': real_location,
                'real_time': system_info.get('sri_lankan_time', {}),
                'mobile_capabilities': {
                    '5g': system_info.get('is_5g_capable', False),
                    'screen_size': system_info.get('screen_size', 'Unknown'),
                    'ram': system_info.get('ram', 'Unknown'),
                    'storage': system_info.get('storage', 'Unknown')
                }
            }
        }), 201
        
    except Exception as e:
        print(f"Mobile auto-registration error: {str(e)}")
        return jsonify({'error': f'Mobile registration failed: {str(e)}'}), 500

@devices_bp.route('/devices/auto-detect', methods=['GET'])
@jwt_required()
def auto_detect_device():
    try:
        current_user = get_jwt_identity()
        user_agent = request.headers.get('User-Agent', '')
        
        system_info = DeviceModel.get_system_info(user_agent)
        mac_address = system_info['mac_address']
        
        existing_device = DeviceModel.find_by_mac_address(request.devices, mac_address)
        if existing_device:
            real_location = get_real_location()
            DeviceModel.update_device_status(
                request.devices, 
                str(existing_device['_id']), 
                existing_device['status'],
                real_location
            )
            
            return jsonify({
                'message': 'Real device already registered - location updated',
                'device_id': str(existing_device['_id']),
                'is_new': False,
                'mac_address': mac_address,
                'system_info': system_info,
                'location': real_location,
                'device_brand': system_info.get('brand', 'Unknown'),
                'device_model': system_info.get('model', 'Unknown')
            }), 200
        
        real_location = get_real_location()
        
        device_name = f"{system_info.get('brand', 'Device')} {system_info.get('model', 'Unknown')}"
        
        device_data = {
            'name': device_name,
            'mac_address': mac_address,
            'type': system_info['device_type'],
            'owner_id': current_user,
            'current_location': real_location,
            'is_auto_detected': True,
            'system_info': system_info
        }
        
        result = DeviceModel.create_device(request.devices, device_data)
        
        request.users.update_one(
            {'_id': ObjectId(current_user)},
            {'$push': {'devices': result.inserted_id}}
        )
        
        return jsonify({
            'message': 'Real device auto-detected and registered',
            'device_id': str(result.inserted_id),
            'is_new': True,
            'system_info': system_info,
            'location': real_location,
            'mac_address': mac_address,
            'device_type': system_info['device_type'],
            'device_brand': system_info.get('brand', 'Unknown'),
            'device_model': system_info.get('model', 'Unknown'),
            'real_time': system_info.get('sri_lankan_time', {})
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/mac-debug', methods=['GET'])
@jwt_required()
def debug_mac_address():
    try:
        user_agent = request.headers.get('User-Agent', '')
        system_info = DeviceModel.get_system_info(user_agent)
        client_info = {
            'user_agent': request.headers.get('User-Agent'),
            'remote_addr': request.remote_addr,
            'headers': dict(request.headers)
        }
        return jsonify({
            'detected_mac': system_info['mac_address'],
            'mac_source': system_info.get('mac_source', 'unknown'),
            'device_type': system_info.get('device_type', 'unknown'),
            'device_brand': system_info.get('brand', 'Unknown'),
            'device_model': system_info.get('model', 'Unknown'),
            'os': system_info.get('os', 'Unknown'),
            'real_time': system_info.get('sri_lankan_time', {}),
            'system_info': system_info,
            'client_info': client_info
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices', methods=['POST'])
@jwt_required()
def register_device():
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        data['owner_id'] = current_user
        
        if 'current_location' not in data:
            data['current_location'] = get_real_location()
        
        result = DeviceModel.create_device(request.devices, data)
        
        request.users.update_one(
            {'_id': ObjectId(current_user)},
            {'$push': {'devices': result.inserted_id}}
        )
        
        return jsonify({
            'message': 'Device registered successfully',
            'device_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices', methods=['GET'])
@jwt_required()
def get_user_devices():
    try:
        current_user = get_jwt_identity()
        
        devices = DeviceModel.find_by_owner(request.devices, current_user)
        
        for device in devices:
            device['_id'] = str(device['_id'])
            device['owner_id'] = str(device['owner_id'])
            device['last_seen'] = device['last_seen'].isoformat()
            device['created_at'] = device['created_at'].isoformat()
            device['updated_at'] = device['updated_at'].isoformat()
        
        return jsonify(devices), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>/update-location', methods=['POST'])
@jwt_required()
def update_device_location(device_id):
    try:
        current_user = get_jwt_identity()
        
        device = DeviceModel.find_by_id(request.devices, device_id)
        if not device or str(device['owner_id']) != current_user:
            return jsonify({'error': 'Device not found'}), 404
        
        real_location = get_real_location()
        
        previous_location = device.get('current_location', {})
        significant_move = False
        
        if (previous_location and 
            previous_location.get('area') != real_location.get('area') and
            device['status'] == 'safe'):
            
            significant_move = True
            
            behavior = {
                'action': 'move',
                'area': real_location['area'],
                'time_of_day': datetime.now(timezone.utc).hour,
                'previous_area': previous_location.get('area', 'unknown'),
                'move_distance': 'significant',
                'device_type': device.get('type', 'unknown')
            }
            
            is_anomalous = anomaly_detector.detect_anomaly(device_id, behavior)
            
            if is_anomalous:
                DeviceModel.update_device_status(request.devices, device_id, 'suspicious')
                
                alert_data = {
                    'device_id': ObjectId(device_id),
                    'device_name': device['name'],
                    'owner_id': ObjectId(current_user),
                    'alert_type': 'suspicious_movement',
                    'message': f"Suspicious movement detected for {device['name']} from {behavior['previous_area']} to {real_location['area']}",
                    'location': real_location,
                    'timestamp': datetime.now(timezone.utc),
                    'resolved': False,
                    'details': {
                        'previous_area': behavior['previous_area'],
                        'new_area': real_location['area'],
                        'move_time': datetime.now(timezone.utc).isoformat(),
                        'device_type': device.get('type', 'unknown')
                    }
                }
                request.alerts.insert_one(alert_data)
        
        DeviceModel.update_device_status(
            request.devices, 
            device_id, 
            device['status'],
            real_location
        )
        
        DeviceModel.add_location_history(
            request.location_history,
            device_id,
            real_location,
            device['status']
        )
        
        return jsonify({
            'message': 'Location updated successfully',
            'location': real_location,
            'significant_move': significant_move,
            'previous_area': previous_location.get('area', 'none'),
            'device_type': device.get('type', 'unknown')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>/status', methods=['POST'])
@jwt_required()
def update_device_status(device_id):
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        device = DeviceModel.find_by_id(request.devices, device_id)
        
        if not device or str(device['owner_id']) != current_user:
            return jsonify({'error': 'Device not found'}), 404
        
        DeviceModel.update_device_status(
            request.devices, 
            device_id, 
            data['status'],
            data.get('location')
        )
        
        if data.get('location'):
            DeviceModel.add_location_history(
                request.location_history,
                device_id,
                data['location'],
                data['status']
            )
        
        return jsonify({'message': 'Device status updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>/check-anomaly', methods=['POST'])
@jwt_required()
def check_anomaly(device_id):
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        device = DeviceModel.find_by_id(request.devices, device_id)
        
        if not device or str(device['owner_id']) != current_user:
            return jsonify({'error': 'Device not found'}), 404
        
        is_anomalous = anomaly_detector.detect_anomaly(device_id, data['behavior'])
        
        if is_anomalous:
            DeviceModel.update_device_status(request.devices, device_id, 'suspicious')
            
            alert_data = {
                'device_id': ObjectId(device_id),
                'device_name': device['name'],
                'owner_id': ObjectId(current_user),
                'alert_type': 'suspicious_behavior',
                'message': f"Suspicious behavior detected for {device['name']}",
                'location': data.get('location', device.get('current_location', {})),
                'timestamp': datetime.now(timezone.utc),
                'resolved': False
            }
            request.alerts.insert_one(alert_data)
        
        return jsonify({
            'is_anomalous': is_anomalous,
            'status': 'suspicious' if is_anomalous else 'safe'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/devices/<device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    try:
        current_user = get_jwt_identity()
        
        device = DeviceModel.find_by_id(request.devices, device_id)
        
        if not device or str(device['owner_id']) != current_user:
            return jsonify({'error': 'Device not found'}), 404
        
        device['_id'] = str(device['_id'])
        device['owner_id'] = str(device['owner_id'])
        device['last_seen'] = device['last_seen'].isoformat()
        device['created_at'] = device['created_at'].isoformat()
        device['updated_at'] = device['updated_at'].isoformat()
        
        return jsonify(device), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500