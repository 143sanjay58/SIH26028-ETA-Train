# AGENTS.md

SIH 2026 prototype (problem statement SIH26028): dynamic ETA / train-delay prediction for Indian Railways. Python ML pipeline (`pandas`/`lightgbm`) wrapped in FastAPI, plus a React/Vite demo dashboard. Everything is a prototype — simulated, no live IR data. No git repo, no CI, no formatter/linter, no `requirements.txt` (deps are installed globally: Python 3.13, pandas 3.0, numpy 2.3, lightgbm 4.7, scikit-learn 1.9, joblib, fastapi, uvicorn, pydantic).

## Commands

- Tests are plain assert scripts, **not pytest**: `python stage13_all_tests.py` (same pattern for every `stage*_all_tests.py` / `stage*_test.py`). Run directly; each step prints `PASS`. Unicode-printing scripts already fixed (see Gotchas).
- Core pipeline singleton tests: `python dynamic_eta_engine.py` or `python eta_predictor.py` (each has `if __name__ == "__main__"`).
- API: `python -m uvicorn api:app --reload` (endpoints `/`, `/health`, `/predict-eta`, `/passenger-assistance`). Must be run from repo root.
- Dashboard: `cd dashboard/STAGE16_FINAL_DASHBOARD; npm install; npm run dev`. React 19 + Vite 7, no TypeScript. Calls `http://127.0.0.1:8000/predict-eta`; falls back to hardcoded demo simulation if unreachable. Demo train is `12303` (route LLH → BEQ → BLY → BZL → DKAE...).

## Architecture / conventions

- ML flow: `ml_ready_segments_final.csv` (frozen route data, ~373k rows) → `feature_builder.py` builds 21 features in a fixed column order (do not reorder) → `eta_predictor.py` loads two pre-trained LightGBM `.joblib` models (`eta_remaining_time_lgbm.joblib`, `future_arrival_delay_lgbm.joblib`) → `dynamic_eta_engine.py` orchestrates, applies ETA consistency correction (a downstream ETA can't precede the previous one + `scheduled_run_minutes`).
- `TrainState` (`train_state.py`) is the universal input. Route semantics: segment `route_order N` connects station N → N+1; a prediction at position P targets `route_order P+1`.
- Station codes are stored upper-case; canonical names live in `*_canonical` columns. Many modules re-derive `train_num_norm` (strip leading zeros from train number) — keep that normalization identical everywhere.
- Stage workflow: `README_STAGE<NN>.txt` documents each stage; each stage ships its own `stage<NN>_pipeline.py` + `stage<NN>_all_tests.py`. New work should follow this pattern and not modify prior stages' engines.
- The dashboard is a presentation layer — do not modify `dynamic_eta_engine.py`, `feature_builder.py`, `eta_predictor.py`, or the `.joblib` files.

## Gotchas

- `api.py` loads `ml_ready_segments_final.csv` and the engines reference repo-root files; run Python from `D:\SIH-2026`.
- `ml_ready_segments.csv` and `ml_ready_segments_final.csv` both exist; all engine/API code uses `_final`.
- The two LightGBM models are pickle artifacts tied to the installed sklearn/lightgbm versions; there is **no training script** in the repo to regenerate them.
- Root holds many generated audit CSVs plus raw SIH data (`ir_train.csv`, `ir_test.csv`, `ir_data_dictionary.csv`, `ir_sample_submission.csv`, duplicated under `indian-railways-predict-train-delay/`). Interpret as outputs/reference, not inputs to edit.
- Stray scratch files (`aaa`, `bbb.py`, `ccc.py`, `ddd.py`, `sample_test1.py`, `sample_test2.py`) are dev cruft, not part of the deliverable.
- **Windows console encoding (real bug, now fixed):** several scripts print unicode (`✓`, `✅`, `❌`) and crashed with `UnicodeEncodeError` on the default cp1252 console. Every script that prints non-ASCII now starts with a `# WINDOWS_CONSOLE_UTF8_FIX` header that reconfigures stdout/stderr to UTF-8, so they run on a plain console. Verified: all `stage9_*`, `stage10_*` scripts and root analysis scripts now `PASS` with no env vars. If you add a new script that prints unicode/emoji, add the same header block (or run with `set PYTHONIOENCODING=utf-8`). The core commands (`stage13_all_tests.py`, `stage14_all_tests.py`, `dynamic_eta_engine.py`, `eta_predictor.py`, `api.py`) never had the bug — their unicode is only in comments — and were left untouched.