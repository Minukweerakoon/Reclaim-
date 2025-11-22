export const generateCampusLocation = () => {
  const campusAreas = [
    { name: 'Library', lat: 40.7128, lng: -74.0060 },
    { name: 'Academic Building', lat: 40.7135, lng: -74.0070 },
    { name: 'Student Center', lat: 40.7120, lng: -74.0055 },
    { name: 'Sports Complex', lat: 40.7140, lng: -74.0080 },
    { name: 'Dormitory A', lat: 40.7115, lng: -74.0090 },
    { name: 'Dormitory B', lat: 40.7150, lng: -74.0045 },
  ];
  
  const randomArea = campusAreas[Math.floor(Math.random() * campusAreas.length)];
  const variation = 0.001;
  
  return {
    latitude: randomArea.lat + (Math.random() - 0.5) * variation,
    longitude: randomArea.lng + (Math.random() - 0.5) * variation,
    area: randomArea.name
  };
};

export const simulateDeviceBehavior = (action) => {
  const hour = new Date().getHours();
  const isNormalTime = hour >= 8 && hour <= 22;
  
  return {
    action: action,
    time_of_day: hour,
    is_weekend: [0, 6].includes(new Date().getDay()),
    area: generateCampusLocation().area,
    is_normal_time: isNormalTime
  };
};

export const getStatusColor = (status) => {
  switch (status) {
    case 'safe': return '#10b981';
    case 'offline': return '#6b7280';
    case 'suspicious': return '#f59e0b';
    case 'stolen': return '#ef4444';
    default: return '#6b7280';
  }
};

export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};