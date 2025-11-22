from datetime import datetime, timezone
from bson import ObjectId
import uuid
import subprocess
import platform
import re
import requests
import json

class DeviceModel:
    @staticmethod
    def get_system_mac_address(user_agent=None):
        try:
            if user_agent and any(keyword in user_agent.lower() for keyword in ['mobile', 'android', 'iphone', 'ipad']):
                return DeviceModel.get_mobile_identifier(user_agent)
            
            if platform.system() == "Windows":
                result = subprocess.check_output('getmac /v /fo csv', shell=True, text=True)
                lines = result.strip().split('\n')
                
                for line in lines[1:]:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        transport_name = parts[0].strip().replace('"', '').lower()
                        mac_address = parts[2].strip().replace('"', '').replace('-', ':')
                        
                        if (mac_address and 
                            mac_address != '00-00-00-00-00-00' and
                            'bluetooth' not in transport_name and
                            'virtual' not in transport_name and
                            'disconnected' not in transport_name.lower()):
                            return mac_address.upper()
                
                result = subprocess.check_output('ipconfig /all', shell=True, text=True)
                lines = result.split('\n')
                current_adapter = None
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('.'):
                        if 'adapter' in line.lower():
                            current_adapter = line
                        elif 'physical address' in line.lower() or 'mac address' in line.lower():
                            if current_adapter and 'virtual' not in current_adapter.lower() and 'bluetooth' not in current_adapter.lower():
                                mac_match = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                                if mac_match:
                                    return mac_match.group(0).replace('-', ':').upper()
            
            elif platform.system() == "Linux":
                try:
                    interfaces = ['eth0', 'wlan0', 'wlp2s0', 'enp0s1']
                    for interface in interfaces:
                        try:
                            result = subprocess.check_output(['cat', f'/sys/class/net/{interface}/address'], text=True)
                            mac = result.strip().upper()
                            if mac and mac != '00:00:00:00:00:00':
                                return mac
                        except:
                            continue
                except:
                    pass
                
            elif platform.system() == "Darwin":
                result = subprocess.check_output(['ifconfig'], text=True)
                for line in result.split('\n'):
                    if 'ether' in line:
                        mac_match = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', line)
                        if mac_match:
                            return mac_match.group(0).upper()
        
        except Exception as e:
            print(f"Error getting MAC address: {e}")
        
        system_info = f"{platform.node()}-{platform.system()}-{platform.release()}"
        unique_id = f"auto-{uuid.uuid5(uuid.NAMESPACE_DNS, system_info).hex[:12].upper()}"
        print(f"Generated unique ID: {unique_id}")
        return unique_id

    @staticmethod
    def get_mobile_identifier(user_agent):
        ua_lower = user_agent.lower()
        
        if 'samsung' in ua_lower:
            if 'galaxy s23' in ua_lower or 'sm-s91' in ua_lower:
                return "SAMSUNG_GALAXY_S23_5G"
            elif 'galaxy s22' in ua_lower or 'sm-s90' in ua_lower:
                return "SAMSUNG_GALAXY_S22_5G"
            elif 'galaxy a54' in ua_lower or 'sm-a546' in ua_lower:
                return "SAMSUNG_GALAXY_A54_5G"
            elif 'galaxy a34' in ua_lower or 'sm-a346' in ua_lower:
                return "SAMSUNG_GALAXY_A34_5G"
            else:
                return "SAMSUNG_ANDROID_PHONE"
        
        elif 'xiaomi' in ua_lower or 'redmi' in ua_lower or 'poco' in ua_lower:
            if 'redmi note 13' in ua_lower:
                return "XIAOMI_REDMI_NOTE_13_5G"
            elif 'poco x6' in ua_lower:
                return "XIAOMI_POCO_X6_5G"
            else:
                return "XIAOMI_ANDROID_PHONE"
        
        elif 'oneplus' in ua_lower:
            if 'oneplus 12' in ua_lower:
                return "ONEPLUS_12_5G"
            elif 'oneplus 11' in ua_lower:
                return "ONEPLUS_11_5G"
            elif 'oneplus nord' in ua_lower:
                return "ONEPLUS_NORD_5G"
            else:
                return "ONEPLUS_ANDROID_PHONE"
        
        elif 'oppo' in ua_lower:
            if 'reno 11' in ua_lower:
                return "OPPO_RENO_11_5G"
            else:
                return "OPPO_ANDROID_PHONE"
        
        elif 'vivo' in ua_lower:
            return "VIVO_ANDROID_PHONE"
        
        elif 'realme' in ua_lower:
            return "REALME_ANDROID_PHONE"
        
        elif 'iphone' in ua_lower:
            if 'iphone 15' in ua_lower:
                return "APPLE_IPHONE_15_PRO"
            elif 'iphone 14' in ua_lower:
                return "APPLE_IPHONE_14_PRO"
            elif 'iphone 13' in ua_lower:
                return "APPLE_IPHONE_13_PRO"
            else:
                return "APPLE_IPHONE"
        
        elif 'ipad' in ua_lower:
            return "APPLE_IPAD"
        
        else:
            return f"MOBILE_{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def detect_device_type(user_agent=None):
        if not user_agent:
            user_agent = requests.utils.default_user_agent()
        
        user_agent_lower = user_agent.lower()
        
        mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'windows phone']
        if any(keyword in user_agent_lower for keyword in mobile_keywords):
            return 'mobile'
        else:
            return 'laptop'

    @staticmethod
    def get_mobile_device_details(user_agent):
        ua_lower = user_agent.lower()
        details = {
            'brand': 'Unknown',
            'model': 'Unknown',
            'os': 'Unknown',
            'os_version': 'Unknown',
            'is_5g_capable': True,
            'screen_size': '6.1 inch',
            'ram': '8GB',
            'storage': '128GB'
        }
        
        if 'android' in ua_lower:
            details['os'] = 'Android'
            if 'android 14' in ua_lower or 'android 15' in ua_lower:
                details['os_version'] = '14+'
            elif 'android 13' in ua_lower:
                details['os_version'] = '13'
            elif 'android 12' in ua_lower:
                details['os_version'] = '12'
            else:
                details['os_version'] = '11 or below'
        
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            details['os'] = 'iOS'
            if 'os 17' in ua_lower or 'ios 17' in ua_lower:
                details['os_version'] = '17'
            elif 'os 16' in ua_lower or 'ios 16' in ua_lower:
                details['os_version'] = '16'
            else:
                details['os_version'] = '15 or below'
        
        if 'samsung' in ua_lower:
            details['brand'] = 'Samsung'
            if 'galaxy s23' in ua_lower:
                details['model'] = 'Galaxy S23 5G'
                details['screen_size'] = '6.1 inch'
                details['ram'] = '8GB'
                details['storage'] = '256GB'
            elif 'galaxy a54' in ua_lower:
                details['model'] = 'Galaxy A54 5G'
                details['screen_size'] = '6.4 inch'
                details['ram'] = '8GB'
                details['storage'] = '128GB'
        
        elif 'xiaomi' in ua_lower or 'redmi' in ua_lower:
            details['brand'] = 'Xiaomi'
            if 'redmi note 13' in ua_lower:
                details['model'] = 'Redmi Note 13 5G'
                details['screen_size'] = '6.67 inch'
                details['ram'] = '8GB'
                details['storage'] = '128GB'
        
        elif 'oneplus' in ua_lower:
            details['brand'] = 'OnePlus'
            if 'oneplus 12' in ua_lower:
                details['model'] = 'OnePlus 12 5G'
                details['screen_size'] = '6.82 inch'
                details['ram'] = '12GB'
                details['storage'] = '256GB'
        
        elif 'iphone' in ua_lower:
            details['brand'] = 'Apple'
            if 'iphone 15' in ua_lower:
                details['model'] = 'iPhone 15 Pro'
                details['screen_size'] = '6.1 inch'
                details['ram'] = '8GB'
                details['storage'] = '128GB'
        
        return details

    @staticmethod
    def get_system_info(user_agent=None):
        if not user_agent:
            user_agent = requests.utils.default_user_agent()
            
        mac_address = DeviceModel.get_system_mac_address(user_agent)
        device_type = DeviceModel.detect_device_type(user_agent)
        
        system_info = {
            'hostname': platform.node(),
            'system': platform.system(),
            'release': platform.release(),
            'processor': platform.processor(),
            'mac_address': mac_address,
            'mac_source': 'detected' if not mac_address.startswith(('auto-', 'mobile-')) else 'mobile-generated',
            'device_type': device_type,
            'user_agent': user_agent,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'real_time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            'sri_lankan_time': DeviceModel.get_sri_lankan_time()
        }
        
        if device_type == 'mobile':
            system_info['is_mobile'] = True
            mobile_details = DeviceModel.get_mobile_device_details(user_agent)
            system_info.update(mobile_details)
            
            if 'android' in user_agent.lower():
                system_info['platform'] = 'android'
                system_info['device_family'] = mobile_details.get('model', 'Android Mobile')
            elif 'iphone' in user_agent.lower() or 'ipad' in user_agent.lower():
                system_info['platform'] = 'ios'
                system_info['device_family'] = mobile_details.get('model', 'Apple Mobile')
            else:
                system_info['platform'] = 'mobile'
                system_info['device_family'] = 'Mobile Device'
        else:
            system_info['is_mobile'] = False
            system_info['platform'] = 'desktop'
            system_info['device_family'] = 'Computer'
            system_info['brand'] = platform.system()
            system_info['model'] = f"{platform.system()} {platform.release()}"
            system_info['os'] = platform.system()
            system_info['os_version'] = platform.release()
            
        print(f"Real system info detected: {system_info}")
        return system_info

    @staticmethod
    def get_sri_lankan_time():
        from datetime import timedelta
        sri_lanka_offset = timedelta(hours=5, minutes=30)
        sri_lanka_time = datetime.now(timezone.utc) + sri_lanka_offset
        return {
            'iso_format': sri_lanka_time.isoformat(),
            'formatted': sri_lanka_time.strftime('%Y-%m-%d %H:%M:%S'),
            'timezone': 'IST (UTC+5:30)'
        }

    @staticmethod
    def create_device(devices_collection, data):
        device_data = {
            'name': data['name'],
            'mac_address': data['mac_address'],
            'type': data['type'],
            'owner_id': ObjectId(data['owner_id']),
            'status': 'safe',
            'current_location': data.get('current_location', {}),
            'normal_locations': [],
            'normal_times': [],
            'is_blacklisted': False,
            'is_auto_detected': data.get('is_auto_detected', False),
            'system_info': data.get('system_info', {}),
            'last_seen': datetime.now(timezone.utc),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        result = devices_collection.insert_one(device_data)
        print(f"Real device created: {data['name']} ({data['mac_address']})")
        return result
    
    @staticmethod
    def update_device_status(devices_collection, device_id, status, location=None):
        update_data = {
            'status': status,
            'updated_at': datetime.now(timezone.utc),
            'last_seen': datetime.now(timezone.utc)
        }
        if location:
            update_data['current_location'] = location
        
        result = devices_collection.update_one(
            {'_id': ObjectId(device_id)},
            {'$set': update_data}
        )
        print(f"Device {device_id} status updated to {status}")
        return result
    
    @staticmethod
    def add_location_history(location_history_collection, device_id, location, status):
        location_data = {
            'device_id': ObjectId(device_id),
            'location': location,
            'status': status,
            'timestamp': datetime.now(timezone.utc)
        }
        result = location_history_collection.insert_one(location_data)
        print(f"Location history added for device {device_id}")
        return result
    
    @staticmethod
    def find_by_id(devices_collection, device_id):
        return devices_collection.find_one({'_id': ObjectId(device_id)})
    
    @staticmethod
    def find_by_owner(devices_collection, owner_id):
        return list(devices_collection.find({'owner_id': ObjectId(owner_id)}))
    
    @staticmethod
    def find_by_mac_address(devices_collection, mac_address):
        device = devices_collection.find_one({'mac_address': mac_address})
        if device:
            print(f"Device found by MAC: {mac_address}")
        else:
            print(f"No device found for MAC: {mac_address}")
        return device