"""
user_profile.py
─────────────────────────────────────────────────────────────
User accessibility profiles for the Oxford LaMB navigation system.

A profile controls two things:
  1. Which vertical transition types are permitted (stairs / elevator).
  2. Per-transition cost multipliers, so that a route that is physically
     possible but difficult carries a higher cost and is avoided unless
     it is the only option.

Profiles
--------
fastest           Regular user. Can use stairs and elevator.
min_effort        Minimises physical effort. Stairs penalised.

Usage
-----
    from user_profile import PROFILES, get_profile

    profile = get_profile("wheelchair")
    allowed = profile.allows_action("STAIR_UP")   # False
    cost    = profile.action_cost_multiplier("ELEVATOR_UP")  # 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, Set


# ─────────────────────────────────────────────────────────────
# PROFILE DATA CLASS
# ─────────────────────────────────────────────────────────────

@dataclass
class UserProfile:
    """
    Accessibility profile for a single user.

    Attributes
    ----------
    name : str
        Machine-readable identifier (e.g. "wheelchair").
    label : str
        Human-readable display name.
    forbidden_actions : set[str]
        Action strings that this profile may never perform.
        The pathfinder will not generate these actions.
    cost_multipliers : dict[str, float]
        Per-action cost scaling applied on top of the base cost.
        Actions not listed here have multiplier 1.0.
        Values > 1 increase cost (discourages use); < 1 decreases cost.
    """
    name              : str
    label             : str
    forbidden_actions : Set[str]            = field(default_factory=set)
    cost_multipliers  : Dict[str, float]    = field(default_factory=dict)

    def allows_action(self, action: str) -> bool:
        """Return True if this action is permitted for this profile."""
        return action not in self.forbidden_actions

    def action_cost_multiplier(self, action: str) -> float:
        """Return the cost multiplier for this action (default 1.0)."""
        return self.cost_multipliers.get(action, 1.0)


# ─────────────────────────────────────────────────────────────
# PROFILE DEFINITIONS
# ─────────────────────────────────────────────────────────────

PROFILES: Dict[str, UserProfile] = {

    # ── Fastest ──────────────────────────────────────────────
    # Pure time minimisation. Costs are already time-calibrated,
    # so the algorithm naturally picks the quickest vertical option.
    "fastest": UserProfile(
        name   = "fastest",
        label  = "Fastest Route",
        forbidden_actions = set(),
        cost_multipliers  = {},
    ),

    # ── Minimum effort ────────────────────────────────────────
    # Minimises physical load. MET-based penalties:
    # stair ascent MET ≈ 8, descent MET ≈ 3, elevator MET ≈ 1.5.
    # Stairs are not forbidden but made significantly more costly.
    "min_effort": UserProfile(
        name   = "min_effort",
        label  = "Minimum Effort",
        forbidden_actions = set(),
        cost_multipliers  = {
            "STAIR_UP"  : 3.0,   # effort penalty: time × 3 (MET ratio ≈ 8/1.5)
            "STAIR_DOWN": 2.0,   # effort penalty: time × 2 (MET ratio ≈ 3/1.5)
        },
    ),

}

# Default profile used when none is specified
DEFAULT_PROFILE = PROFILES["fastest"]


# ─────────────────────────────────────────────────────────────
# LOOKUP HELPER
# ─────────────────────────────────────────────────────────────

def get_profile(name: str) -> UserProfile:
    """
    Return the UserProfile for `name`.
    Falls back to the default profile if `name` is unrecognised.
    """
    return PROFILES.get(name, DEFAULT_PROFILE)


# ─────────────────────────────────────────────────────────────
# ALIASES  (for query resolver / LLM integration)
# ─────────────────────────────────────────────────────────────

PROFILE_ALIASES: Dict[str, str] = {
    # English
    "fastest"           : "fastest",
    "fast"              : "fastest",
    "quickest"          : "fastest",
    "min_effort"        : "min_effort",
    "minimum effort"    : "min_effort",
    "least effort"      : "min_effort",
    "easy"              : "min_effort",
    "standard"          : "fastest",
    "normal"            : "fastest",
    "regular"           : "fastest",
    "able-bodied"       : "fastest",
    # Turkish
    "en hızlı"          : "fastest",
    "hızlı"             : "fastest",
    "en az efor"        : "min_effort",
    "az eforlu"         : "min_effort",
    "kolay"             : "min_effort",
    "standart"          : "fastest",
    "normal kullanıcı"  : "fastest",
}


def resolve_profile(text: str) -> UserProfile:
    """
    Map a free-text description to a UserProfile.
    Case-insensitive. Falls back to standard if not recognised.
    """
    key = text.strip().lower()
    profile_name = PROFILE_ALIASES.get(key, "fastest")
    return PROFILES[profile_name]
