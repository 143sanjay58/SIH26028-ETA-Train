"""
SIH26028 ETA intelligence core, embedded UNMODIFIED from D:\\SIH-2026.

The validated LightGBM ETA pipeline lives in this directory as flat modules
(dynamic_eta_engine.py, eta_predictor.py, feature_builder.py,
upcoming_stations.py, train_state.py, eta_response.py, eta_confidence.py,
delay_impact.py). Those modules use absolute imports between each other and
resolve their data files (ml_ready_segments_final.csv + *.joblib) from the
directory of __file__.

To embed them here without altering a single line of the validated core, this
package inserts its own directory at the front of sys.path so the flat
absolute imports resolve to THIS copy. Importing this package is cheap: the
heavy network CSV + LightGBM models are loaded lazily by SIHETAService (see
service.py), never at app import time.
"""
import os
import sys

_SIH_ETA_DIR = os.path.dirname(os.path.abspath(__file__))

if _SIH_ETA_DIR not in sys.path:
    sys.path.insert(0, _SIH_ETA_DIR)

# Core version marker (mirrors the reference implementation tag)
CORE_VERSION = "STAGE13"