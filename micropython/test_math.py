
import math

def compute_mean_from_true_anomaly(true_anomaly_deg, eccentricity):
    """
    Compute Mean Anomaly from True Anomaly.
    
    Args:
        true_anomaly_deg: True Anomaly in degrees (0360)
        eccentricity: Orbital eccentricity (0.0 to 0.9)
        
    Returns:
        Mean Anomaly in radians (0 to 2pi)
    """
    if eccentricity < 1e-6:
        return math.radians(true_anomaly_deg)
        
    nu = math.radians(true_anomaly_deg)
    
    # tan(E/2) = sqrt((1-e)/(1+e)) * tan(nu/2)
    term1 = math.sqrt((1.0 - eccentricity) / (1.0 + eccentricity))
    term2 = math.tan(nu / 2.0)
    
    # Use atan to find E/2, then multiply by 2
    # Note: nu/2 is in range [0, 180] (if nu 0-360) or [-180, 180]
    # We want E to be in the same quadrant/half-plane
    E_half = math.atan(term1 * term2)
    E = 2.0 * E_half
    
    # Handle wrapping if input was normalized funny, but atan handles principal range
    # M = E - e*sin(E)
    M = E - eccentricity * math.sin(E)
    
    # Normalize to 0-2pi
    M = M % (2.0 * math.pi)
    return M

# Test cases
e = 0.5
print(f"Eccentricity: {e}")
for nu_deg in [0, 90, 180, 270]:
    M = compute_mean_from_true_anomaly(nu_deg, e)
    M_deg = math.degrees(M)
    print(f"Nu: {nu_deg:5.1f} -> M: {M_deg:5.1f}")
