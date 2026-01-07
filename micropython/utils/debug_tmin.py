
import satellite_position
import time
from sgp4 import SGP4

def test():
    print("Testing t_min calculation...")
    
    # Epoch: 2023-11-20 13:08:40 (Day 324.5479)
    epoch_year = 23
    epoch_day = 324.54791667
    
    # 1. Test Epoch Time
    # 2023-11-20 13:08:40 UTC
    try:
        t_epoch_unix = time.mktime((2023, 11, 20, 13, 8, 40, 0, 324))
        print(f"Epoch Unix (Target): {t_epoch_unix}")
    except:
        t_epoch_unix = 1700485720
        print(f"Epoch Unix (Hardcoded): {t_epoch_unix}")

    # 2. Test t_min at Epoch
    t_tuple = time.gmtime(t_epoch_unix)
    # Pad to 9
    t_tuple = tuple(list(t_tuple)[:8] + [0]) 
    
    # Mock SGP4 object
    sgp4 = SGP4()
    # just init with dummies, n=15.5
    sgp4.init(epoch_year, epoch_day, 0, 0, 0, 0, 0, 0, 15.5)
    
    res = satellite_position.compute_satellite_geodetic(sgp4, epoch_year, epoch_day, t_tuple)
    print(f"At Epoch (t=0): t_min = {res.get('t_min')} (Expected ~0.0)")
    
    # 3. Test t_min at Epoch + 60 min
    t_next_unix = t_epoch_unix + 3600
    t_tuple_next = time.gmtime(t_next_unix)
    t_tuple_next = tuple(list(t_tuple_next)[:8] + [0])
    
    res = satellite_position.compute_satellite_geodetic(sgp4, epoch_year, epoch_day, t_tuple_next)
    print(f"At Epoch + 60m: t_min = {res.get('t_min')} (Expected ~60.0)")
    
    # 4. Debug Internal Values if possible
    # We can't see inside the function easily, but the result tells us.

if __name__ == "__main__":
    test()
