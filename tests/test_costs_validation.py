"""
test_costs_validation.py
─────────────────────────────────────────────────────────────
Validates the elevator cost model against the stair breakeven
point: the elevator should be cheaper than stairs only when
the floor span is ≥ 2 floors (accounting for the one-time
boarding penalty).

Assertions
----------
1. For a 1-floor trip, stairs are cheaper than elevator
   (boarding overhead outweighs the per-floor savings).
2. For a 2-floor trip, elevator is cheaper than stairs.
3. FLOOR_CHANGE_SECONDS["elevator_entry"] == 25
4. FLOOR_CHANGE_SECONDS["elevator_floor"] == 5
5. Breakeven is between 1 and 2 floors.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pathfinding.costs import (
    COST_ELEVATOR_ENTRY,
    COST_ELEVATOR_FLOOR,
    COST_STAIR_UP,
    FLOOR_CHANGE_SECONDS,
)


def elevator_cost(floors: int) -> float:
    return COST_ELEVATOR_ENTRY + COST_ELEVATOR_FLOOR * floors


def stair_cost(floors: int) -> float:
    return COST_STAIR_UP * floors


def test_floor_change_seconds_keys():
    assert "elevator_entry" in FLOOR_CHANGE_SECONDS, \
        "FLOOR_CHANGE_SECONDS missing 'elevator_entry'"
    assert "elevator_floor" in FLOOR_CHANGE_SECONDS, \
        "FLOOR_CHANGE_SECONDS missing 'elevator_floor'"
    assert FLOOR_CHANGE_SECONDS["elevator_entry"] == 25
    assert FLOOR_CHANGE_SECONDS["elevator_floor"] == 5


def test_single_floor_stair_wins():
    elev = elevator_cost(1)
    stair = stair_cost(1)
    assert stair < elev, (
        f"Expected stairs ({stair:.1f}) < elevator ({elev:.1f}) for 1 floor"
    )


def test_two_floor_elevator_wins():
    elev = elevator_cost(2)
    stair = stair_cost(2)
    assert elev < stair, (
        f"Expected elevator ({elev:.1f}) < stairs ({stair:.1f}) for 2 floors"
    )


def test_breakeven_between_one_and_two():
    breakeven = COST_ELEVATOR_ENTRY / (COST_STAIR_UP - COST_ELEVATOR_FLOOR)
    assert 1.0 < breakeven < 2.0, (
        f"Breakeven expected between 1 and 2 floors, got {breakeven:.3f}"
    )


if __name__ == "__main__":
    tests = [
        test_floor_change_seconds_keys,
        test_single_floor_stair_wins,
        test_two_floor_elevator_wins,
        test_breakeven_between_one_and_two,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ✗  {t.__name__}: UNEXPECTED {type(e).__name__}: {e}")

    breakeven = COST_ELEVATOR_ENTRY / (COST_STAIR_UP - COST_ELEVATOR_FLOOR)
    print()
    print(f"  Elevator entry  : {COST_ELEVATOR_ENTRY:.1f} units  "
          f"(≈ {FLOOR_CHANGE_SECONDS['elevator_entry']} s)")
    print(f"  Elevator/floor  : {COST_ELEVATOR_FLOOR:.1f} units  "
          f"(≈ {FLOOR_CHANGE_SECONDS['elevator_floor']} s)")
    print(f"  Stair up/floor  : {COST_STAIR_UP:.1f} units  "
          f"(≈ {FLOOR_CHANGE_SECONDS['stair_up']} s)")
    print(f"  Breakeven       : {breakeven:.3f} floors")
    print()
    print(f"  {passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)
