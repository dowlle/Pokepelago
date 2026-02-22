import os
import sys
import subprocess
import tempfile
import shutil
import json
import glob
import zipfile
from logic_emulator import PokepelagoEmulator

ARCHIPELAGO_EXE = r"C:\ProgramData\Archipelago\ArchipelagoGenerate.exe"
TIMEOUT_SECONDS = 180

def run_yaml_file(yaml_path):
    """Generates a seed and runs the emulator for a single YAML path."""
    tmpdir = tempfile.mkdtemp(prefix="ap_emu_")
    outdir = os.path.join(tmpdir, "output")
    os.makedirs(outdir, exist_ok=True)
    
    # Copy yaml to tmpdir to ensure it's the only one generated
    target_yaml = os.path.join(tmpdir, "test.yaml")
    shutil.copy(yaml_path, target_yaml)
    
    try:
        cmd = [
            ARCHIPELAGO_EXE, 
            "--multi", "1", 
            "--player_files", tmpdir,
            "--outputpath", outdir,
            "--spoiler", "3"
        ]
        # Run generation
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        
        if result.returncode != 0:
            return "FAILED_GEN", 0
            
        emu = None
        # Priority 1: JSON spoiler from output/tmp
        spoilers = glob.glob(os.path.join(tmpdir, "**", "*.json"), recursive=True)
        if spoilers:
            with open(spoilers[0], "r") as f:
                spoiler_data = json.load(f)
            emu = PokepelagoEmulator(spoiler_data, is_json=True)
        else:
            # Priority 2: Extract from ZIP
            zips = glob.glob(os.path.join(outdir, "*.zip"))
            if zips:
                with zipfile.ZipFile(zips[0], 'r') as z:
                    namelist = z.namelist()
                    # Try JSON inside zip
                    json_files = [f for f in namelist if f.endswith(".json")]
                    if json_files:
                        z.extract(json_files[0], tmpdir)
                        with open(os.path.join(tmpdir, json_files[0]), "r") as f:
                            spoiler_data = json.load(f)
                        emu = PokepelagoEmulator(spoiler_data, is_json=True)
                    else:
                        # Try TXT inside zip
                        spoiler_txt_files = [f for f in namelist if f.endswith("_Spoiler.txt") or f == "spoiler.txt"]
                        if spoiler_txt_files:
                            z.extract(spoiler_txt_files[0], tmpdir)
                            with open(os.path.join(tmpdir, spoiler_txt_files[0]), "r") as st:
                                txt_content = st.read()
                                from logic_emulator import parse_spoiler_txt
                                spoiler_data = parse_spoiler_txt(txt_content)
                                emu = PokepelagoEmulator(spoiler_data, is_json=False)

        if not emu:
            return "FAILED_SPOILER", 0
            
        # Run sweep
        success = emu.run_sweep()
        count = len(emu.caught_pokemon)
        
        if success:
            return "PASS", count
        else:
            return "STUCK", count

    except subprocess.TimeoutExpired:
        return "TIMEOUT", 0
    except Exception as e:
        print(f"Error processing {os.path.basename(yaml_path)}: {e}")
        return f"ERROR ({type(e).__name__})", 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    yaml_dir = os.path.join(os.path.dirname(__file__), "test_yamls")
    yaml_files = glob.glob(os.path.join(yaml_dir, "*.yaml"))
    
    if not yaml_files:
        print(f"No YAML files found in {yaml_dir}")
        sys.exit(1)
        
    print(f"Starting batch test on {len(yaml_files)} YAMLs...")
    print("-" * 60)
    print(f"{'YAML File':<25} | {'Result':<15} | {'Pokemon'}")
    print("-" * 60)
    
    results = []
    for y in sorted(yaml_files):
        name = os.path.basename(y)
        res, count = run_yaml_file(y)
        print(f"{name:<25} | {res:<15} | {count}")
        results.append((name, res, count))
        
    print("-" * 60)
    passes = sum(1 for _, res, _ in results if res == "PASS")
    print(f"SUMMARY: {passes}/{len(results)} Passed")
    
    if passes < len(results):
        sys.exit(1)
