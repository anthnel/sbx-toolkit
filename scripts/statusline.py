#!/usr/bin/env python3
import json, subprocess, sys

SEP = " · "
ESC = "\033"

def red(t):  return f"{ESC}[31m{t}{ESC}[0m"
def cyan(t): return f"{ESC}[36m{t}{ESC}[0m"

def git_branch():
    for cmd in (
        ["git", "branch", "--show-current"],
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    ):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
            if out and out != "HEAD":
                return out
        except Exception:
            pass
    return None

def pct_str(value, label):
    v = round(value)
    s = f"{label}:{v}%"
    return red(s) if v >= 80 else s

data = json.load(sys.stdin)

sid   = (data.get("session_id") or "????????")[:8]
m     = data.get("model") or {}
model = m.get("display_name") or m.get("id") or "?"

ctx_raw = (data.get("context_window") or {}).get("used_percentage")
ctx_str = pct_str(ctx_raw, "ctx") if ctx_raw is not None else "ctx:--"

rl = data.get("rate_limits") or {}
rate_parts = []
for key, label in [("five_hour", "5h"), ("seven_day", "7d")]:
    pct = (rl.get(key) or {}).get("used_percentage")
    if pct is not None:
        rate_parts.append(pct_str(pct, label))

parts = [f"[{sid}]", model]

branch = git_branch()
if branch:
    parts.append(cyan(branch))

parts.append(ctx_str)
parts.extend(rate_parts)

print(SEP.join(parts))
