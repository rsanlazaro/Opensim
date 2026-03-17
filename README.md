# OpenSim Gait Analysis Pipeline

This project implements a complete biomechanical analysis pipeline using OpenSim and Python. It processes motion capture data through five sequential steps: Scaling, Inverse Kinematics, Residual Reduction Analysis, Inverse Dynamics, and Static Optimization.

---

## Project Structure

```
opensim_project/
├── opensimFiles/
│   └── Gait2354_Simbody/
│       ├── gait2354_simbody.osim           # Generic model
│       ├── gait2354_Scale_MarkerSet.xml    # Marker set for scaling
│       ├── gait2354_RRA_Actuators.xml      # RRA actuator definitions
│       ├── gait2354_RRA_Tasks.xml          # RRA tracking tasks
│       ├── subject01_static.trc            # Static trial marker data
│       ├── subject01_walk1.trc             # Walking trial marker data
│       └── subject01_walk1_grf.mot         # Ground reaction forces
├── results/
│   ├── scaling/                            # Scaling outputs
│   ├── ik/                                 # IK outputs
│   ├── rra/                                # RRA outputs
│   ├── id/                                 # ID outputs
│   └── so/                                 # SO outputs
└── scripts/
    ├── pipeline.py                         # Runs all steps sequentially
    ├── scaling.py                          # Step 1: Model scaling
    ├── ik.py                               # Step 2: Inverse kinematics
    ├── rra.py                              # Step 3: Residual reduction
    ├── id.py                               # Step 4: Inverse dynamics
    ├── so.py                               # Step 5: Static optimization
    └── rra_worker.py                       # Worker script for RRA subprocess
```

---

## Requirements

- Python 3.10
- OpenSim 4.5.2 (`opensim` conda environment)
- NumPy
- SciPy

Install dependencies inside the `opensim` conda environment:

```bash
conda activate opensim
conda install scipy
```

---

## Running the Pipeline

### Option 1 — Run the full pipeline automatically

Execute all five steps in sequence by running `pipeline.py`. If any step fails, the pipeline stops immediately and reports which step failed.

```bash
cd opensim_project
python scripts/pipeline.py
```

### Option 2 — Run each step individually

Each script can be run independently. They must be executed from the **project root directory** (`opensim_project/`) and in the correct order, as each step depends on outputs from the previous one.

```bash
cd opensim_project

python scripts/scaling.py   # Step 1
python scripts/ik.py        # Step 2
python scripts/rra.py       # Step 3
python scripts/id.py        # Step 4
python scripts/so.py        # Step 5
```

---

## Pipeline Steps

### Step 1 — Scaling (`scaling.py`)

Scales the generic Gait2354 model to match the subject's body dimensions using a static trial.

**Inputs:**
- `gait2354_simbody.osim` — generic model
- `gait2354_Scale_MarkerSet.xml` — marker definitions
- `subject01_static.trc` — static standing trial

**Outputs** (`results/scaling/`):
- `scaled_model.osim` — subject-specific scaled model
- `static_pose.mot` — static pose motion file
- `model_with_markers.osim` — intermediate model with markers applied

---

### Step 2 — Inverse Kinematics (`ik.py`)

Computes joint angles from marker trajectories using least-squares marker tracking.

**Inputs:**
- `results/scaling/scaled_model.osim`
- `subject01_walk1.trc` — walking trial marker data

**Outputs** (`results/ik/`):
- `subject01_walk1_ik.mot` — joint angle trajectories
- `subject01_walk1_ik_marker_errors.sto` — marker tracking errors
- `subject01_walk1_ik_model_marker_locations.sto` — model marker positions

---

### Step 3 — Residual Reduction Analysis (`rra.py`)

Adjusts kinematics to be dynamically consistent with the measured ground reaction forces, reducing residual forces and moments at the pelvis.

**Inputs:**
- `results/scaling/scaled_model.osim`
- `results/ik/subject01_walk1_ik.mot`
- `subject01_walk1_grf.mot`
- `gait2354_RRA_Actuators.xml`
- `gait2354_RRA_Tasks.xml`

**Outputs** (`results/rra/`):
- `subject01_simbody_adjusted.osim` — mass-adjusted model
- `rra_Kinematics_q.sto` — RRA-adjusted joint angles
- `rra_Actuation_force.sto` — residual and reserve forces
- `rra_setup.xml` — generated setup file
- `external_loads.xml` — generated GRF configuration

> **Note:** RRA runs via a worker subprocess (`rra_worker.py`) to work around a known crash in the OpenSim 4.5 Python bindings on Windows. `rra_worker.py` must be present in the same `scripts/` folder.

---

### Step 4 — Inverse Dynamics (`id.py`)

Computes net joint moments and forces using Newton-Euler equations applied to the scaled model and IK kinematics.

**Inputs:**
- `results/scaling/scaled_model.osim`
- `results/ik/subject01_walk1_ik.mot`
- `subject01_walk1_grf.mot`

**Outputs** (`results/id/`):
- `subject01_walk1_id.sto` — joint moments and forces
- `id_setup.xml` — generated setup file
- `external_loads.xml` — generated GRF configuration

---

### Step 5 — Static Optimization (`so.py`)

Resolves the muscle redundancy problem by computing individual muscle forces and activations at each time frame.

**Inputs:**
- `results/scaling/scaled_model.osim`
- `results/ik/subject01_walk1_ik.mot`
- `subject01_walk1_grf.mot`

**Outputs** (`results/so/`):
- `so_StaticOptimization_activation.sto` — muscle activations (0–1)
- `so_StaticOptimization_force.sto` — muscle forces (N)
- `scaled_model_strong.osim` — muscle-strengthened model used for SO
- `ik_upsampled.sto` — filtered and upsampled kinematics (600 Hz)
- `so_setup.xml` — generated setup file
- `external_loads.xml` — generated GRF configuration
- `reserve_actuators.xml` — generated reserve actuator definitions

> **Note:** SO uses the raw IK kinematics filtered at 6 Hz and upsampled to 600 Hz using a 4th-order Butterworth filter and cubic spline interpolation. Muscle strength is scaled 3× globally (5× for iliacus and psoas) and the MTP and subtalar joints are locked to prevent fictitious accelerations from near-zero IK signals.

---

## Output Summary

| Step | Key Output File | Description |
|------|----------------|-------------|
| Scaling | `results/scaling/scaled_model.osim` | Subject-specific model |
| IK | `results/ik/subject01_walk1_ik.mot` | Joint angles |
| RRA | `results/rra/rra_Kinematics_q.sto` | Corrected joint angles |
| ID | `results/id/subject01_walk1_id.sto` | Joint moments |
| SO | `results/so/so_StaticOptimization_activation.sto` | Muscle activations |

---

## Notes

- All scripts must be run from the **project root directory**, not from inside `scripts/`.
- The `pipeline.py` script handles the working directory automatically.
- The `.vtp` geometry warnings during model loading are cosmetic and do not affect results — they indicate missing mesh files for visualization only.
- Subject mass is set to **75 kg** in `scaling.py`. Change `scale_tool.setSubjectMass(75)` to match your subject.