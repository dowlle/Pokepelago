"""
Batch generation test for Pokepelago APWorld.

Tests all 8 lock combos (dexsanity × region_lock × type_locks) with the default
goal, then tests each of the 4 goal types with the hardest lock combo
(dex=ON, reg=ON, type=ON). Total: 8 + 4 = 12 configs.

Usage:
    python tests/test_all_configs.py
"""
import os
import sys
import subprocess
import tempfile
import time
import shutil

ARCHIPELAGO_EXE = r"C:\ProgramData\Archipelago\ArchipelagoGenerate.exe"
TIMEOUT_SECONDS = 90  # per-config timeout

YAML_TEMPLATE = """\
name: Pokepelago
description: Auto-test config
game: pokepelago
pokepelago:
  progression_balancing: 50
  accessibility: full
  gen1: true
  gen2: true
  gen3: true
  gen4: false
  gen5: false
  gen6: false
  gen7: false
  gen8: false
  gen9: false
  shadows: 'on'
  enable_dexsanity: {dexsanity}
  enable_region_lock: {region_lock}
  type_locks: {type_locks}
  type_lock_mode: any
  legendary_gating: {legendary_gating}
  goal: {goal}
  goal_amount: {goal_amount}
  goal_region: {goal_region}
  starting_pokemon_count: 5
  starting_type_unlocks: 2
  starting_region_unlocks: 1
"""


def run_config(label: str, yaml_vars: dict) -> dict:
    """Run a single generation and return result dict."""
    safe_label = label.replace(" ", "_").replace("=", "_")
    tmpdir = tempfile.mkdtemp(prefix=f"pokepelago_{safe_label}_")
    yaml_path = os.path.join(tmpdir, "Pokepelago.yaml")
    with open(yaml_path, "w") as f:
        f.write(YAML_TEMPLATE.format(**yaml_vars))

    start = time.time()
    try:
        result = subprocess.run(
            [ARCHIPELAGO_EXE, "--multi", "1", "--player_files", tmpdir],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        elapsed = time.time() - start
        combined = (result.stdout or "") + (result.stderr or "")

        if result.returncode == 0 and "FillError" not in combined and "Error" not in combined:
            status = "PASS"
            detail = f"{elapsed:.1f}s"
        else:
            if "FillError" in combined:
                status = "FILL_ERROR"
                for line in combined.split("\n"):
                    if "FillError" in line or "No more spots" in line:
                        detail = line.strip()[:80]
                        break
                else:
                    detail = "FillError (see log)"
            else:
                status = "ERROR"
                for line in combined.split("\n"):
                    if "Error" in line or "Exception" in line:
                        detail = line.strip()[:80]
                        break
                else:
                    detail = f"exit={result.returncode}"

        log_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"gen_{safe_label}.log"
        )
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(combined)

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        status = "TIMEOUT"
        detail = f">{TIMEOUT_SECONDS}s (killed)"
        log_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"gen_{safe_label}.log"
        )
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"TIMEOUT after {TIMEOUT_SECONDS}s\n")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return {"label": label, "status": status, "detail": detail, "elapsed": elapsed}


def main():
    results = []

    # --- Part 1: All 8 lock combos with default goal (any_pokemon) ---
    print("=" * 75)
    print("Part 1: Lock combinations (goal=any_pokemon)")
    print("=" * 75)
    base_vars = dict(
        legendary_gating=50, goal="any_pokemon",
        goal_amount=200, goal_region="kanto"
    )
    combos = [(d, r, t)
              for d in (False, True)
              for r in (False, True)
              for t in (False, True)]

    for i, (dex, reg, typ) in enumerate(combos, 1):
        label = f"Dex={'ON' if dex else 'OFF'} Reg={'ON' if reg else 'OFF'} Type={'ON' if typ else 'OFF'}"
        print(f"  [{i}/8] {label} ...", end=" ", flush=True)
        v = {**base_vars,
             "dexsanity": str(dex).lower(),
             "region_lock": str(reg).lower(),
             "type_locks": str(typ).lower()}
        r = run_config(label, v)
        results.append(r)
        icon = {"PASS": "✅", "FILL_ERROR": "❌", "TIMEOUT": "⏰", "ERROR": "💥"}.get(r["status"], "?")
        print(f"{icon} {r['status']} — {r['detail']}")

    # --- Part 2: All 4 goals with hardest combo (dex+reg+type ON) ---
    print()
    print("=" * 75)
    print("Part 2: Goal types (dex=ON, reg=ON, type=ON)")
    print("=" * 75)
    goal_tests = [
        ("Goal=any_pokemon",       dict(goal="any_pokemon",       goal_amount=200, goal_region="kanto", legendary_gating=50)),
        ("Goal=percentage",        dict(goal="percentage",        goal_amount=50,  goal_region="kanto", legendary_gating=50)),
        ("Goal=region_completion", dict(goal="region_completion", goal_amount=200, goal_region="kanto", legendary_gating=0)),
        ("Goal=all_legendaries",   dict(goal="all_legendaries",   goal_amount=200, goal_region="kanto", legendary_gating=0)),
    ]
    for i, (label, goal_vars) in enumerate(goal_tests, 1):
        print(f"  [{i}/4] {label} ...", end=" ", flush=True)
        v = {**goal_vars,
             "dexsanity": "true",
             "region_lock": "true",
             "type_locks": "true"}
        r = run_config(label, v)
        results.append(r)
        icon = {"PASS": "✅", "FILL_ERROR": "❌", "TIMEOUT": "⏰", "ERROR": "💥"}.get(r["status"], "?")
        print(f"{icon} {r['status']} — {r['detail']}")

    # --- Summary ---
    print()
    print("=" * 75)
    print(f"{'Config':<40} {'Status':<12} {'Time':<10}")
    print("-" * 75)
    for r in results:
        print(f"{r['label']:<40} {r['status']:<12} {r['elapsed']:.1f}s")
    print("=" * 75)

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\n{passed}/{total} configs passed.")

    if passed < total:
        print("\nFailing configs — check gen_*.log files in tests/ for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
