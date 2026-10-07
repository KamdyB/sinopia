"""Every threshold the scoring rules use, in one labelled place.

PROVISIONAL VALUES. Not one number below is validated. They need cited
sources from the sports science literature before this tool flags
anything outside a demo, and none may be invented for that purpose.
Until then every level produced from these values is a prompt for a
coach conversation, never a finding.
"""

# Weeks of tracked history required before load rules apply at all.
MIN_BASELINE_WEEKS = 3

# Trailing weekly windows of her own history averaged into the baseline.
BASELINE_WEEKS = 4

# Weekly load above this multiple of her own baseline triggers act.
LOAD_JUMP_RATIO = 1.5

# Check-in entries required before wellness drift is evaluated.
MIN_WELLNESS_ENTRIES = 6

# How many of the most recent check-ins form the recent side of the drift.
WELLNESS_RECENT_ENTRIES = 3

# Drift margin on the 1 to 5 check-in scale, where 5 is best.
WELLNESS_DRIFT_MARGIN = 1.0
