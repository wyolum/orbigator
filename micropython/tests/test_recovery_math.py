"""
Recovery Math Verification (Offline)
=====================================
Tests the "stitch" logic for multi-turn recovery.
Logic: reconstruct absolute position from a saved checkpoint and current phase.
"""

def recover_abs_ticks(current_phase_ticks, saved_abs_ticks):
    """
    Recover absolute ticks.
    current_phase_ticks: 0-4095 (raw reading from motor)
    saved_abs_ticks: last known absolute position
    """
    CPR = 4096
    saved_phase = saved_abs_ticks % CPR
    
    # Calculate shortest delta between phases
    # delta is the movement since last checkpoint, in -2048..2047 range
    delta = (current_phase_ticks - saved_phase + CPR//2) % CPR - CPR//2
    
    return saved_abs_ticks + delta

def test_recovery():
    print("Testing recovery math...")
    
    cases = [
        # (saved_abs, current_phase, expected_abs)
        (1000, 1010, 1010),     # Small forward move
        (1000, 990, 990),       # Small backward move
        (4000, 100, 4196),      # Forward wrap (4000 -> 4095 -> 0 -> 100)
        (100, 4000, -96),       # Backward wrap (100 -> 0 -> 4095 -> 4000)
        (40960, 100, 41060),    # Multi-turn forward wrap
        (40960, 4000, 40864),   # Multi-turn backward wrap
    ]
    
    passed = 0
    for saved, current, expected in cases:
        result = recover_abs_ticks(current, saved)
        if result == expected:
            print(f"  ✓ Saved={saved}, Current={current} -> Result={result} (PASS)")
            passed += 1
        else:
            print(f"  ✗ Saved={saved}, Current={current} -> Result={result} (FAIL, expected {expected})")
            
    print(f"\nResults: {passed}/{len(cases)} passed")
    return passed == len(cases)

if __name__ == "__main__":
    test_recovery()
