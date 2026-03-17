import opensim as osim
import os
import subprocess
import sys

# -----------------------------
# Input files
# -----------------------------

scaled_model_file = "results/scaling/scaled_model.osim"
ik_mot_file       = "results/ik/subject01_walk1_ik.mot"
grf_mot_file      = "./opensimFiles/Gait2354_Simbody/subject01_walk1_grf.mot"
actuators_file    = "./opensimFiles/Gait2354_Simbody/gait2354_RRA_Actuators.xml"
tasks_file        = "./opensimFiles/Gait2354_Simbody/gait2354_RRA_Tasks.xml"

# -----------------------------
# Output directory
# -----------------------------

output_dir = "results/rra"
os.makedirs(output_dir, exist_ok=True)

a = os.path.abspath

# ------------------------------------------------
# Step 1: Get time range from IK file
# ------------------------------------------------

ik_table    = osim.TimeSeriesTable(a(ik_mot_file))
ik_times    = ik_table.getIndependentColumn()
print(f"IK file range: {ik_times[0]:.3f}s → {ik_times[-1]:.3f}s ({len(ik_times)} frames)")

grf_table   = osim.TimeSeriesTable(a(grf_mot_file))
grf_times   = grf_table.getIndependentColumn()
print(f"GRF file range: {grf_times[0]:.3f}s → {grf_times[-1]:.3f}s ({len(grf_times)} frames)")
start_time = 0.1   # skip the first 0.1s
end_time   = 1.6   # one gait cycle

print(f"Time range: {start_time:.3f}s → {end_time:.3f}s")

# ------------------------------------------------
# Step 2: Write external loads XML
# ------------------------------------------------

ext_loads_file = a(os.path.join(output_dir, "external_loads.xml"))
with open(ext_loads_file, "w") as f:
    f.write(f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <ExternalLoads name="ext_loads">
        <objects>
            <ExternalForce name="Right_GRF">
                <applied_to_body>calcn_r</applied_to_body>
                <force_expressed_in_body>ground</force_expressed_in_body>
                <point_expressed_in_body>ground</point_expressed_in_body>
                <force_identifier>ground_force_v</force_identifier>
                <point_identifier>ground_force_p</point_identifier>
                <torque_identifier>ground_torque_</torque_identifier>
            </ExternalForce>
            <ExternalForce name="Left_GRF">
                <applied_to_body>calcn_l</applied_to_body>
                <force_expressed_in_body>ground</force_expressed_in_body>
                <point_expressed_in_body>ground</point_expressed_in_body>
                <force_identifier>1_ground_force_v</force_identifier>
                <point_identifier>1_ground_force_p</point_identifier>
                <torque_identifier>1_ground_torque_</torque_identifier>
            </ExternalForce>
        </objects>
        <groups />
        <datafile>{a(grf_mot_file)}</datafile>
    </ExternalLoads>
</OpenSimDocument>
""")
print(f"Saved external loads → {ext_loads_file}")

# ------------------------------------------------
# Step 3: Write RRA setup XML
# ------------------------------------------------

setup_file = a(os.path.join(output_dir, "rra_setup.xml"))
with open(setup_file, "w") as f:
    f.write(f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <RRATool name="rra">
        <model_file>{a(scaled_model_file)}</model_file>
        <replace_force_set>true</replace_force_set>
        <force_set_files>{a(actuators_file)}</force_set_files>
        <results_directory>{a(output_dir)}</results_directory>
        <output_precision>8</output_precision>
        <initial_time>{start_time}</initial_time>
        <final_time>{end_time}</final_time>
        <maximum_number_of_integrator_steps>20000</maximum_number_of_integrator_steps>
        <maximum_integrator_step_size>1</maximum_integrator_step_size>
        <minimum_integrator_step_size>1e-8</minimum_integrator_step_size>
        <integrator_error_tolerance>1e-5</integrator_error_tolerance>
        <solve_for_equilibrium_for_auxiliary_states>false</solve_for_equilibrium_for_auxiliary_states>
        <external_loads_file>{ext_loads_file}</external_loads_file>
        <desired_kinematics_file>{a(ik_mot_file)}</desired_kinematics_file>
        <task_set_file>{a(tasks_file)}</task_set_file>
        <lowpass_cutoff_frequency>-1</lowpass_cutoff_frequency>
        <adjust_com_to_reduce_residuals>false</adjust_com_to_reduce_residuals>
        <adjusted_com_body>torso</adjusted_com_body>
        <output_model_file>{a(os.path.join(output_dir, "subject01_simbody_adjusted.osim"))}</output_model_file>
    </RRATool>
</OpenSimDocument>
""")
print(f"Saved RRA setup → {setup_file}")

# ------------------------------------------------
# Step 4: Run via opensim-cmd from conda environment
# ------------------------------------------------

conda_env = os.path.dirname(sys.executable)
print(f"Searching from: {conda_env}")

for root, dirs, files in os.walk(os.path.join(conda_env, "..")):
    for f in files:
        if "opensim-cmd" in f.lower():
            print("opensim_cmd:\n")
            print(os.path.join(root, f)) # ← find path for opensim_cmd

opensim_cmd = r"C:\Users\L03508435\AppData\Local\anaconda3\envs\opensim\..\opensim\Library\bin\opensim-cmd.exe"  # ← paste path found above

print("Running RRA...")
result = subprocess.run(
    [opensim_cmd, "run-tool", setup_file],
    text=True,
    cwd=os.path.dirname(os.path.abspath(__file__))
)

if result.returncode == 0:
    print("RRA complete")
else:
    print(f"RRA failed with return code {result.returncode}")