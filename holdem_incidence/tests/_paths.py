"""Locations of the independent reference implementations used as oracles (read-only)."""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

KUHN3_DIR = os.environ.get("KUHN3_DIR", r"C:\Users\raosa\Documents\Codex\2026-08-27\implement-3-player-kuhn-poker-exactly\outputs\kuhn3")
AUDIT_PATH = os.environ.get("AUDIT_PATH", r"C:\Users\raosa\Documents\Codex\2026-10-16\find-x20\outputs\holdem_bridge_audit.py")
REPO_DIR = os.environ.get("POKER_REPO", r"C:\Users\raosa\OneDrive\Documents\poker")


def load_kuhn3():
    if not os.path.isdir(KUHN3_DIR):
        return None
    if KUHN3_DIR not in sys.path:
        sys.path.insert(0, KUHN3_DIR)
    import kuhn3  # noqa
    return kuhn3


def load_audit():
    if not os.path.isfile(AUDIT_PATH):
        return None
    spec = importlib.util.spec_from_file_location("holdem_bridge_audit", AUDIT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_repo_kuhn3p():
    path = os.path.join(REPO_DIR, "kuhn3p.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("repo_kuhn3p", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def config(name):
    import json
    with open(os.path.join(ROOT, "configs", name), encoding="utf-8") as f:
        return json.load(f)
