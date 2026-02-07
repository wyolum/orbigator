from dataclasses import dataclass
from datetime import datetime, timezone

CPR = 4096
GEAR = 14 / 120
SIGN = -1  # +motor => -EQX


def wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


@dataclass(slots=True)
class EQXState:
    last_eqx: float
    last_motor_encoder_count: int
    last_cache_time: datetime

    @classmethod
    def capture(cls, eqx: float, encoder_ext: int) -> "EQXState":
        return cls(eqx, encoder_ext, datetime.now(timezone.utc))


def recover_delta_counts_unique(m0: int, m1: int, *, motor_direction: int) -> int:
    """
    Unique delta recovery assuming:
        - |delta| < 1 motor revolution
        - direction is constant
    """
    d_mod = (m1 - m0) % CPR

    if d_mod == 0:
        return 0

    if motor_direction > 0:
        return d_mod
    else:
        return d_mod - CPR


def delta_eqx_from_counts(delta_counts: int) -> float:
    return SIGN * (delta_counts / CPR) * 360.0 * GEAR


def recover_eqx_from_mod(cache, current_mod: int, *, motor_direction: int):
    m0 = cache.last_motor_encoder_count % CPR
    d_counts = recover_delta_counts_unique(m0, current_mod, motor_direction=motor_direction)
    eqx = wrap180(cache.last_eqx + delta_eqx_from_counts(d_counts))
    return eqx, d_counts


# -------------------------------
# Test Harness
# -------------------------------

def simulate_case(name, last_ext, move_counts, motor_direction):
    """
    last_ext: cached extended encoder
    move_counts: true motion after cache (simulate reality)
    """
    print(f"\n=== {name} ===")

    # pretend this was the cached state
    last_eqx = 10.0
    cache = EQXState.capture(last_eqx, last_ext)

    # simulate actual motion
    true_ext = last_ext + move_counts
    current_mod = true_ext % CPR

    recovered_eqx, recovered_counts = recover_eqx_from_mod(
        cache,
        current_mod,
        motor_direction=motor_direction
    )

    print("cached mod:", last_ext % CPR)
    print("current mod:", current_mod)
    print("true delta counts:", move_counts)
    print("recovered delta:", recovered_counts)

    if recovered_counts == move_counts:
        print("✅ counts match")
    else:
        print("❌ mismatch")

    print("recovered EQX:", recovered_eqx)


if __name__ == "__main__":

    # choose the direction your tracking uses
    MOTOR_DIRECTION = +1   # try flipping to -1

    base_encoder = 10 * CPR + 1000  # arbitrary extended count

    simulate_case(
        "Small forward motion",
        last_ext=base_encoder,
        move_counts=300,
        motor_direction=MOTOR_DIRECTION
    )

    simulate_case(
        "Forward wrap-around",
        last_ext=base_encoder,
        move_counts=1500,   # crosses modulo boundary
        motor_direction=MOTOR_DIRECTION
    )

    simulate_case(
        "No movement",
        last_ext=base_encoder,
        move_counts=0,
        motor_direction=MOTOR_DIRECTION
    )

    # Now test backward direction
    MOTOR_DIRECTION = -1

    simulate_case(
        "Small backward motion",
        last_ext=base_encoder,
        move_counts=-250,
        motor_direction=MOTOR_DIRECTION
    )

    simulate_case(
        "Backward wrap-around",
        last_ext=base_encoder,
        move_counts=-1800,
        motor_direction=MOTOR_DIRECTION
    )
