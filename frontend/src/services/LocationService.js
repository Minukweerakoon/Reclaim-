class LocationService {
    constructor() {
        this.watchId = null;
        this.isTracking = false;
        this.lastLocation = null;
    }

    // Get precise location using browser GPS
    async getPreciseLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported'));
                return;
            }

            const options = {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            };

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const location = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        altitude: position.coords.altitude,
                        heading: position.coords.heading,
                        speed: position.coords.speed,
                        timestamp: position.timestamp
                    };
                    resolve(location);
                },
                (error) => {
                    reject(error);
                },
                options
            );
        });
    }

    // Start continuous location tracking
    startLiveTracking(deviceId, onLocationUpdate) {
        if (!navigator.geolocation) {
            console.error('Geolocation not supported');
            return false;
        }

        const options = {
            enableHighAccuracy: true,
            timeout: 5000,
            maximumAge: 0
        };

        this.watchId = navigator.geolocation.watchPosition(
            async (position) => {
                const location = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    heading: position.coords.heading,
                    speed: position.coords.speed,
                    timestamp: position.timestamp
                };

                this.lastLocation = location;
                
                // Send heartbeat to server
                try {
                    const response = await fetch(`/api/devices/${deviceId}/location-heartbeat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token')}`
                        },
                        body: JSON.stringify({
                            geolocation: location
                        })
                    });

                    if (response.ok) {
                        onLocationUpdate && onLocationUpdate(location);
                    }
                } catch (error) {
                    console.error('Failed to send location update:', error);
                }
            },
            (error) => {
                console.error('Location tracking error:', error);
            },
            options
        );

        this.isTracking = true;
        return true;
    }

    // Stop location tracking
    stopLiveTracking() {
        if (this.watchId !== null) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
            this.isTracking = false;
        }
    }

    // Get Sri Lankan time
    getSriLankanTime() {
        // Sri Lanka is UTC+5:30
        const now = new Date();
        const sriLankaOffset = 5.5 * 60 * 60 * 1000; // 5.5 hours in milliseconds
        const sriLankaTime = new Date(now.getTime() + sriLankaOffset);
        
        return {
            iso: sriLankaTime.toISOString(),
            formatted: sriLankaTime.toLocaleString('en-US', {
                timeZone: 'Asia/Colombo',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }),
            timezone: 'Asia/Colombo'
        };
    }

    // Calculate distance between two coordinates in meters
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371e3; // Earth radius in meters
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lon2 - lon1) * Math.PI / 180;

        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                Math.cos(φ1) * Math.cos(φ2) *
                Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

        return R * c;
    }
}

export default new LocationService();