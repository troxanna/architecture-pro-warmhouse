from flask import Flask, request, jsonify
from datetime import datetime
import random

app = Flask(__name__)

# Mapping between sensor IDs and locations
SENSOR_LOCATION_MAP = {
    "1": "Living Room",
    "2": "Bedroom",
    "3": "Kitchen"
}

LOCATION_SENSOR_MAP = {
    "Living Room": "1",
    "Bedroom": "2",
    "Kitchen": "3"
}


def get_location_from_sensor(sensor_id):
    """Get location based on sensor ID"""
    return SENSOR_LOCATION_MAP.get(sensor_id, "Unknown")


def get_sensor_from_location(location):
    """Get sensor ID based on location"""
    return LOCATION_SENSOR_MAP.get(location, "0")


@app.route('/temperature', methods=['GET'])
def get_temperature():
    """Get temperature for a specific location or sensor ID"""
    location = request.args.get('location', '')
    sensor_id = request.args.get('sensorId', '')
    
    # If no location is provided, use a default based on sensor ID
    if not location:
        if sensor_id:
            location = get_location_from_sensor(sensor_id)
        else:
            location = "Unknown"
    
    # If no sensor ID is provided, generate one based on location
    if not sensor_id:
        sensor_id = get_sensor_from_location(location)
    
    # Generate random temperature between 18 and 28 degrees
    temperature = round(random.uniform(18.0, 28.0), 2)
    
    response = {
        "value": temperature,
        "unit": "C",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "location": location,
        "status": "active",
        "sensor_id": sensor_id,
        "sensor_type": "temperature",
        "description": f"Temperature sensor in {location}"
    }
    
    return jsonify(response)


@app.route('/temperature/<sensor_id>', methods=['GET'])
def get_temperature_by_id(sensor_id):
    """Get temperature for a specific sensor ID"""
    location = get_location_from_sensor(sensor_id)
    
    # Generate random temperature between 18 and 28 degrees
    temperature = round(random.uniform(18.0, 28.0), 2)
    
    response = {
        "value": temperature,
        "unit": "C",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "location": location,
        "status": "active",
        "sensor_id": sensor_id,
        "sensor_type": "temperature",
        "description": f"Temperature sensor in {location}"
    }
    
    return jsonify(response)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
