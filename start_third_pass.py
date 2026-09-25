"""Windowless launcher for the third pass: sets the run's environment and hands
over to runenumc, with no console for anything to Ctrl+C.
Run as:  pythonw.exe start_third_pass.py
"""
import os, sys, runpy
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("KUHN_MODE", "nash")
os.environ.setdefault("KUHN_ORDER", "bet")
os.environ.setdefault("KUHN_CAP", "7200")
os.environ.setdefault("KUHN_LOG", "log_runenumc_task.txt")
sys.argv = ["runenumc.py", "20"]
runpy.run_path("runenumc.py", run_name="__main__")
