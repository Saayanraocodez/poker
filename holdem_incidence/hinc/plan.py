"""The declared analysis plan.  Every analysis script reads its thresholds from here, and
``scripts/preregister.py`` writes them (with config hashes and a timestamp) BEFORE any panel
profile is trained or examined.  Changing a value here after results exist must be recorded as an
amendment in ``results/preregistration.json``.
"""

# --- candidate selection (by residual, never by incidence) -----------------------------------
# A trained profile is analysed iff its AVERAGE-strategy NashConv <= SELECT_NASHCONV_PER_POT *
# initial pot (bb).  Every run that passes is analysed; failing runs are reported, not analysed.
SELECT_NASHCONV_PER_POT = 1e-3

# --- numerical tolerances (bb) ---------------------------------------------------------------
TOL_NUM = 1e-12          # float64 full-enumeration floor for an exact zero
TOL_EQ_FACTOR = 10.0     # |D_A| <= 10 * max_i r_i  -> "unresolved"
TOL_CROSS = 1e-9         # |cross effect| above this counts as a cross effect
TOL_NUMERATOR = 1e-9     # |D_X(theta*)| above this counts as a non-vanishing numerator
TOL_FAMILY = 1e-9        # along a family, r_i(theta) <= r_i(baseline) + TOL_FAMILY counts as kept

# --- reach classes ---------------------------------------------------------------------------
REACH_RARE = 1e-6        # 0 < reach <= REACH_RARE -> "rare";  reach == 0.0 exactly -> "unreached"

# --- off-path scan ---------------------------------------------------------------------------
# theta candidates: binary information sets with total reach <= REACH_RARE.
# upstream deviations: binary information sets U of a DIFFERENT player whose history followed by
# U's aggressive action is a prefix of theta's history (the deviation leads into theta's history).
# Directions are mass moves passive -> aggressive at U; theta is the aggressive probability at theta.
FAMILY_WINDOW = 0.05     # the equilibrium condition is checked on theta* +- 0.05 (kept side)
FAMILY_GRID = 11         # points checked inside that window

# --- training budget (fixed after the smoke measurement, before any panel result) ------------
PILOT = {"game": "configs/expanded24.json", "variants": ["cfr+", "dcfr"], "seeds": [1, 2, 3, 4, 5, 6],
         "iterations": 30000}
PANEL = {"variants": ["dcfr"], "seeds": [1, 2, 3], "iterations": 12000}
CHECKPOINTS = [10, 30, 100, 300, 1000, 3000, 6000, 12000, 20000, 30000]
CONTROL = {"game": "configs/control_2p.json", "variants": ["cfr+"], "seeds": [1, 2], "iterations": 5000}
