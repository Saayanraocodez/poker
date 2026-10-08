"""Windowless launcher for the (3,5) silent-cell exact enumeration (k35/enumc7.py, resumable).
usage:  pythonw.exe start_k35silent.py"""
import os, sys, subprocess
os.chdir(os.path.dirname(os.path.abspath(__file__)))
env = dict(os.environ, KUHN_CARDS="5", KUHN_MODE="nash", KUHN_ORDER="bet", KUHN_CKPT="300")
with open("log_enumc7_k5c7_silentN.txt", "a") as f:
    f.write("===== relaunched by start_k35silent.py\n"); f.flush()
    subprocess.call([sys.executable, "-u", "enumc7.py", "a11:0,a21:0,a31:0,a41:0,a51:0", "22", "k5c7_silentN"],
                    stdout=f, stderr=subprocess.STDOUT, env=env)
