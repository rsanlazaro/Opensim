import opensim as osim
import os
import numpy as np
from scipy import signal
from scipy.interpolate import CubicSpline

# -----------------------------
# Input files
# -----------------------------

scaled_model_file = "results/scaling/scaled_model.osim"
ik_mot_file       = "results/ik/subject01_walk1_ik.mot"
grf_mot_file      = "./opensimFiles/Gait2354_Simbody/subject01_walk1_grf.mot"

# -----------------------------
# Output directory
# -----------------------------

output_dir = "results/so"
os.makedirs(output_dir, exist_ok=True)

a = os.path.abspath

# ------------------------------------------------
# Step 1: Scale muscles + lock noisy joints
# ------------------------------------------------

model = osim.Model(a(scaled_model_file))
model.initSystem()

# Scale muscles
strength_scale = 3.0
extra_scale = {
    "iliacus_r": 5.0, "iliacus_l": 5.0,
    "psoas_r":   5.0, "psoas_l":   5.0,
}
muscles = model.getMuscles()
for i in range(muscles.getSize()):
    muscle = muscles.get(i)
    name   = muscle.getName()
    scale  = extra_scale.get(name, strength_scale)
    muscle.setMaxIsometricForce(muscle.getMaxIsometricForce() * scale)

# Lock joints that have near-zero motion in IK
# (mtp and subtalar cause huge fictitious accelerations)
joints_to_lock = [
    "mtp_angle_r", "mtp_angle_l",
    "subtalar_angle_r", "subtalar_angle_l"
]
coord_set = model.getCoordinateSet()
for i in range(coord_set.getSize()):
    coord = coord_set.get(i)
    if coord.getName() in joints_to_lock:
        coord.set_locked(True)
        print(f"  Locked: {coord.getName()}")

strong_model_file = a(os.path.join(output_dir, "scaled_model_strong.osim"))
model.printToXML(strong_model_file)
print(f"Saved model → {strong_model_file}")

# ------------------------------------------------
# Step 2: Filter + upsample IK using scipy
# ------------------------------------------------

storage = osim.Storage(a(ik_mot_file))
n_rows  = storage.getSize()

times = []
data  = []

for i in range(n_rows):
    sv  = storage.getStateVector(i)
    t   = sv.getTime()
    row = [sv.getData().get(j) for j in range(sv.getSize())]
    times.append(t)
    data.append(row)

times = np.array(times)
data  = np.array(data)

# Sample rate of original data
fs = 1.0 / np.mean(np.diff(times))
print(f"Original sample rate: {fs:.1f} Hz")

# Apply 4th order low-pass Butterworth filter at 6 Hz
cutoff = 6.0
sos = signal.butter(4, cutoff / (fs / 2), btype='lowpass', output='sos')
filtered = np.zeros_like(data)
for col in range(data.shape[1]):
    filtered[:, col] = signal.sosfiltfilt(sos, data[:, col])

# Upsample to 600 Hz using cubic spline on filtered data
new_times = np.arange(times[0], times[-1], 1.0 / 600.0)
upsampled = np.zeros((len(new_times), data.shape[1]))
for col in range(data.shape[1]):
    cs = CubicSpline(times, filtered[:, col])
    upsampled[:, col] = cs(new_times)

# Write as proper .sto file
upsampled_file = a(os.path.join(output_dir, "ik_upsampled.sto"))
n_cols = storage.getColumnLabels().getSize()
labels = [storage.getColumnLabels().get(i) for i in range(n_cols)]

with open(upsampled_file, "w") as f:
    f.write("Coordinates\n")
    f.write("version=1\n")
    f.write(f"nRows={len(new_times)}\n")
    f.write(f"nColumns={len(labels)}\n")
    f.write("inDegrees=yes\n")
    f.write("endheader\n")
    f.write("\t".join(labels) + "\n")
    for i, t in enumerate(new_times):
        row = "\t".join([f"{t:.8f}"] + [f"{upsampled[i,j]:.8f}" for j in range(upsampled.shape[1])])
        f.write(row + "\n")

print(f"Filtered at {cutoff} Hz + upsampled: {len(new_times)} frames → {upsampled_file}")

start_time = float(new_times[0])  + 0.1
end_time   = float(new_times[-1]) - 0.1
print(f"Time range: {start_time:.3f}s → {end_time:.3f}s")

# ------------------------------------------------
# Step 3: Write reserve actuators XML
# ------------------------------------------------

reserve_file = a(os.path.join(output_dir, "reserve_actuators.xml"))
with open(reserve_file, "w") as f:
    f.write("""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <ForceSet name="reserve_actuators">
        <objects>
            <CoordinateActuator name="reserve_pelvis_tx">
                <coordinate>pelvis_tx</coordinate>
                <optimal_force>100</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_pelvis_ty">
                <coordinate>pelvis_ty</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_pelvis_tz">
                <coordinate>pelvis_tz</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_pelvis_tilt">
                <coordinate>pelvis_tilt</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_pelvis_list">
                <coordinate>pelvis_list</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_pelvis_rotation">
                <coordinate>pelvis_rotation</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_lumbar_extension">
                <coordinate>lumbar_extension</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_lumbar_bending">
                <coordinate>lumbar_bending</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
            <CoordinateActuator name="reserve_lumbar_rotation">
                <coordinate>lumbar_rotation</coordinate>
                <optimal_force>1</optimal_force>
                <min_control>-infinity</min_control>
                <max_control>infinity</max_control>
            </CoordinateActuator>
        </objects>
        <groups />
    </ForceSet>
</OpenSimDocument>
""")
print(f"Saved reserve actuators → {reserve_file}")

# ------------------------------------------------
# Step 4: Write external loads XML
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
# Step 5: Write SO setup XML
# ------------------------------------------------

setup_file = a(os.path.join(output_dir, "so_setup.xml"))
with open(setup_file, "w") as f:
    f.write(f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <AnalyzeTool name="so">
        <model_file>{strong_model_file}</model_file>
        <force_set_files>{reserve_file}</force_set_files>
        <replace_force_set>false</replace_force_set>
        <results_directory>{a(output_dir)}</results_directory>
        <output_precision>8</output_precision>
        <initial_time>{start_time}</initial_time>
        <final_time>{end_time}</final_time>
        <in_degrees>true</in_degrees>
        <solve_for_equilibrium_for_auxiliary_states>false</solve_for_equilibrium_for_auxiliary_states>
        <maximum_number_of_integrator_steps>20000</maximum_number_of_integrator_steps>
        <maximum_integrator_step_size>1</maximum_integrator_step_size>
        <minimum_integrator_step_size>1e-8</minimum_integrator_step_size>
        <integrator_error_tolerance>1e-5</integrator_error_tolerance>
        <external_loads_file>{ext_loads_file}</external_loads_file>
        <coordinates_file>{upsampled_file}</coordinates_file>
        <lowpass_cutoff_frequency_for_coordinates>-1</lowpass_cutoff_frequency_for_coordinates>
        <AnalysisSet>
            <objects>
                <StaticOptimization name="StaticOptimization">
                    <start_time>{start_time}</start_time>
                    <end_time>{end_time}</end_time>
                    <step_interval>1</step_interval>
                    <in_degrees>true</in_degrees>
                    <use_model_force_set>true</use_model_force_set>
                    <activation_exponent>2</activation_exponent>
                    <use_articulation_weight_set>false</use_articulation_weight_set>
                    <optimizer_convergence_criterion>1e-3</optimizer_convergence_criterion>
                    <optimizer_max_iterations>1000</optimizer_max_iterations>
                </StaticOptimization>
            </objects>
            <groups />
        </AnalysisSet>
    </AnalyzeTool>
</OpenSimDocument>
""")
print(f"Saved SO setup → {setup_file}")

# ------------------------------------------------
# Step 6: Run Static Optimization
# ------------------------------------------------

print("Running Static Optimization...")
try:
    so_tool = osim.AnalyzeTool(setup_file)
    success = so_tool.run()
    if success:
        print("Static Optimization complete")
    else:
        print("Static Optimization failed")
except Exception as e:
    print(f"Static Optimization exception: {e}")

print("Script finished")