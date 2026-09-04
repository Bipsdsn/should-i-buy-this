#!/usr/bin/env python3
"""One-command launcher for the Should-I-Buy-This MVP.

Usage:  python run.py     (or double-click start.bat on Windows)

Runs from its own folder, checks for a Groq key (env var or .streamlit/secrets.toml),
and starts the Streamlit app with the browser opening automatically.
"""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
os.chdir(HERE)

has_secret = (HERE / ".streamlit" / "secrets.toml").exists()
has_env = bool(os.environ.get("GROQ_API_KEY"))
if not (has_secret or has_env):
    print("\n[i] No Groq key found — the app will run in HONEST FALLBACK mode (no live AI).")
    print("    To enable AI verdicts: create .streamlit/secrets.toml with:")
    print('        GROQ_API_KEY = "your_free_key_from_console.groq.com"\n')
else:
    print("\n[i] Groq key found — live AI verdicts enabled.\n")

print("[i] Starting… your browser will open at http://localhost:8501 (Ctrl+C to stop).\n")
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.headless=false", "--server.port=8501"])
