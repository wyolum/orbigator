# Motion Profile Tuning Guide

## Overview

The DYNAMIXEL motors support smooth motion profiles that eliminate jerky movement. This is controlled by two parameters:

- **Profile Velocity**: Controls maximum speed during movement
- **Profile Acceleration**: Controls how quickly the motor accelerates/decelerates

## Default Settings

The motors are initialized with these default values:
```python
velocity = 50       # Moderate speed limit
acceleration = 20   # Smooth acceleration
```

## Tuning Guidelines

### For Smoother Motion (Less Jerky)
- **Increase** Profile Acceleration (e.g., 30-50)
  - Higher values = slower, gentler acceleration
  - Makes starts and stops very smooth
  
- **Increase** Profile Velocity (e.g., 70-100)
  - Higher values = slower maximum speed
  - Reduces abrupt movements

### For Faster Response (More Responsive)
- **Decrease** Profile Acceleration (e.g., 5-15)
  - Lower values = quicker acceleration
  - Motor responds faster to commands
  
- **Decrease** Profile Velocity (e.g., 20-40)
  - Lower values = higher maximum speed
  - Faster movements

### For Maximum Speed (No Smoothing)
```python
velocity = 0        # No speed limit
acceleration = 0    # No acceleration limit
```
**Warning**: This will make motion very jerky!

## How to Adjust

### Method 1: Change Default in Code

Edit `dynamixel_motor.py`, line ~57:
```python
self.set_motion_profile(velocity=50, acceleration=20)
```

Change the values to your preference.

### Method 2: Adjust After Initialization

In `orbigator.py`, after motor initialization:
```python
# Make AoV motor extra smooth
aov_motor.set_motion_profile(velocity=80, acceleration=40)

# Make EQX motor more responsive
eqx_motor.set_motion_profile(velocity=30, acceleration=15)
```

### Method 3: Dynamic Adjustment

Add to your main loop or state machine:
```python
# Smooth mode for precise positioning
if current_state in [1, 2]:  # Setup states
    aov_motor.set_motion_profile(velocity=80, acceleration=40)

# Faster mode for running simulation
elif current_state == 3:  # Running state
    aov_motor.set_motion_profile(velocity=40, acceleration=20)
```

## Recommended Profiles

### For AoV Motor (Pointer Arm)
```python
# Extra smooth (recommended for visible pointer)
aov_motor.set_motion_profile(velocity=60, acceleration=30)
```

### For EQX Motor (Orbital Plane)
```python
# Moderate smooth (slower movements anyway due to gearing)
eqx_motor.set_motion_profile(velocity=40, acceleration=20)
```

## Value Ranges

- **Valid range**: 0 to 32767
- **Practical range**: 0 to 200
- **Recommended range**: 10 to 100

## Testing

To test different profiles:
1. Upload modified code to Pico
2. Watch the motor movement during encoder adjustments
3. Adjust values up or down based on feel
4. Repeat until motion feels smooth and responsive

## Notes

- Profile settings are stored in RAM, not EEPROM
- Settings reset on power cycle
- Each motor can have different profiles
- Changes take effect immediately on next movement command
