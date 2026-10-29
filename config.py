"""
Configuration file for robot control system.
Adjust these values based on your specific hardware setup.
"""

# Flask server settings
FLASK_HOST = '0.0.0.0'  # Listen on all interfaces
FLASK_PORT = 8080       # Using 8080 since 5000 may be blocked by network

# Maestro servo controller settings
MAESTRO_PORT = '/dev/ttyACM0'  # Adjust based on your setup

# Servo channel assignments (adjust to match your wiring)
SERVO_CHANNELS = {
    'left_wheel': 0,
    'right_wheel': 1,
    'head_tilt': 3,
    'head_pan': 4,
    'waist': 2,
    # Right arm channels 5-10
    'right_shoulder1': 5,
    'right_shoulder2': 6,
    'right_elbow': 7,
    'right_wrist_bend': 8,
    'right_wrist_rotate': 9,
    'right_gripper': 10,
    # Left arm channels 11-16
    'left_shoulder1': 11,
    'left_shoulder2': 12,
    'left_elbow': 13,
    'left_wrist_bend': 14,
    'left_wrist_rotate': 15,
    'left_gripper': 16,
}

# Servo limits (in Maestro units: typically 4000-8000, center ~6000)
# IMPORTANT: Adjust these after testing your specific servos!
SERVO_LIMITS = {
    'left_wheel': {
        'min': 4000,
        'max': 8000,
        'center': 6000,  # Neutral/stop position for continuous rotation
        'forward_min': 6600,  # At or above this = forward (higher = faster)
        'forward_max': 7000,  # Max forward speed
        'reverse_min': 5400,  # At or below this = reverse (lower = faster)
        'reverse_max': 5000,  # Max reverse speed
    },
    'right_wheel': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
        'forward_min': 6605,
        'forward_max': 7100,  # Max forward speed
        'reverse_min': 5395,
        'reverse_max': 4900,  # Max reverse speed
    },
    'head_tilt': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'head_pan': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'waist': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
        #TODO: Recalibrate arms 
    # Right arm - calibrated values
    'right_shoulder1': {
        'min': 4000,
        'max': 10000,
        'center': 6000,
    },
    'right_shoulder2': {
        'min': 4000,
        'max': 8000,
        'center': 5000,
    },
    'right_elbow': {
        'min': 4000,
        'max': 10000,
        'center': 6000,
    },
    'right_wrist_bend': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'right_wrist_rotate': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'right_gripper': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    # Left arm - defaults, calibrate later
    'left_shoulder1': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'left_shoulder2': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'left_elbow': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'left_wrist_bend': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'left_wrist_rotate': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
    },
    'left_gripper': {
        'min': 4000,
        'max': 8000,
        'center': 6000,
},
}


# Head position helpers (servo is a maestro.Controller; returns Maestro units)
def get_head_pan(servo):
    return servo.getPosition(SERVO_CHANNELS['head_pan'])


def get_head_tilt(servo):
    return servo.getPosition(SERVO_CHANNELS['head_tilt'])
