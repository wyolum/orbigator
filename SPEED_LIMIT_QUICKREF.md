# Speed Limit Quick Reference

## Current Settings

In `orbigator.py`, after motor initialization:
```python
aov_motor.set_speed_limit(velocity=150)  # AoV (pointer arm)
eqx_motor.set_speed_limit(velocity=100)  # LAN (orbital plane)
```

## How It Works

**Profile Velocity** controls maximum motor speed:
- **0** = No limit (FAST! Not recommended)
- **50-100** = Moderate speed (good for testing)
- **100-200** = Slow, safe speed (recommended for display)
- **200+** = Very slow (may be too slow for real-time simulation)

**Remember**: Higher values = SLOWER movement

## Adjusting Speed

### Make It Slower (Safer)
Increase the velocity value:
```python
aov_motor.set_speed_limit(velocity=200)  # Very slow
eqx_motor.set_speed_limit(velocity=150)  # Slower
```

### Make It Faster (More Responsive)
Decrease the velocity value:
```python
aov_motor.set_speed_limit(velocity=80)   # Faster
eqx_motor.set_speed_limit(velocity=50)   # Much faster
```

### Remove Speed Limit (Not Recommended!)
```python
aov_motor.set_speed_limit(velocity=0)    # No limit - FAST!
```

## Recommended Values

### For Display/Demo
```python
aov_motor.set_speed_limit(velocity=150)  # Slow, visible motion
eqx_motor.set_speed_limit(velocity=100)  # Moderate
```

### For Testing
```python
aov_motor.set_speed_limit(velocity=80)   # Faster for quick tests
eqx_motor.set_speed_limit(velocity=60)   # Faster
```

### For Time-Lapse
```python
aov_motor.set_speed_limit(velocity=50)   # Fast for time-lapse
eqx_motor.set_speed_limit(velocity=30)   # Fast
```

## Notes

- Speed limits are set in RAM, not EEPROM (reset on power cycle)
- Changes take effect immediately on next movement command
- Each motor can have different speed limits
- EQX motor is already slower due to 10.909:1 gearing
- AoV motor should generally be slower than LAN for smooth, visible motion
