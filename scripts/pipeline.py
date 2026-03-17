import subprocess
import sys
import os

# -----------------------------
# Pipeline configuration
# -----------------------------

scripts_dir = os.path.dirname(os.path.abspath(__file__))

pipeline = [
    ("Scaling",               os.path.join(scripts_dir, "scaling.py")),
    ("Inverse Kinematics",    os.path.join(scripts_dir, "ik.py")),
    ("Residual Reduction",    os.path.join(scripts_dir, "rra.py")),
    ("Inverse Dynamics",      os.path.join(scripts_dir, "id.py")),
    ("Static Optimization",   os.path.join(scripts_dir, "so.py")),
]

# -----------------------------
# Run pipeline
# -----------------------------

print("=" * 60)
print("OpenSim Pipeline")
print("=" * 60)

for step, (name, script) in enumerate(pipeline, 1):
    print(f"\n[Step {step}/5] {name}")
    print("-" * 60)

    if not os.path.exists(script):
        print(f"ERROR: Script not found → {script}")
        print("Pipeline aborted.")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, script],
        text=True,
        cwd=os.path.dirname(scripts_dir)   # run from project root
    )

    if result.returncode != 0:
        print(f"\nERROR: {name} failed with return code {result.returncode}")
        print("Pipeline aborted.")
        sys.exit(1)

    print(f"[Step {step}/5] {name} — DONE")

print("\n" + "=" * 60)
print("Pipeline complete — all steps finished successfully")
print("=" * 60)