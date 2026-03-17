import opensim as osim
import os

# -----------------------------
# Input files
# -----------------------------

scaled_model_file = "results/scaling/scaled_model.osim"
walk_trc          = "./opensimFiles/Gait2354_Simbody/subject01_walk1.trc"

# -----------------------------
# Output directory
# -----------------------------

output_dir = "results/ik"
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------------
# Step 1: Load the scaled model
# ------------------------------------------------

model = osim.Model(scaled_model_file)
model.initSystem()
print(f"Loaded scaled model with {model.getMarkerSet().getSize()} markers")

# ------------------------------------------------
# Step 2: Configure the IK tool
# ------------------------------------------------

ik_tool = osim.InverseKinematicsTool()
ik_tool.setModel(model)
ik_tool.setMarkerDataFileName(walk_trc)
ik_tool.set_report_marker_locations(True)

# ------------------------------------------------
# Step 3: Build IK tasks from model markers dynamically
# ------------------------------------------------

ik_task_set = ik_tool.getIKTaskSet()

for i in range(model.getMarkerSet().getSize()):
    marker_name = model.getMarkerSet().get(i).getName()
    ik_marker_task = osim.IKMarkerTask()
    ik_marker_task.setName(marker_name)
    ik_marker_task.setWeight(1.0)
    ik_marker_task.setApply(True)
    ik_task_set.cloneAndAppend(ik_marker_task)

print(f"Created {ik_task_set.getSize()} IK marker tasks")

# ------------------------------------------------
# Step 4: Set time range from the TRC file
# ------------------------------------------------

trc_table  = osim.TimeSeriesTableVec3(walk_trc)
start_time = trc_table.getIndependentColumn()[0]
end_time   = trc_table.getIndependentColumn()[-1]

ik_tool.setStartTime(start_time)
ik_tool.setEndTime(end_time)

print(f"IK time range: {start_time:.3f}s → {end_time:.3f}s")

# ------------------------------------------------
# Step 5: Set output
# ------------------------------------------------

ik_output = os.path.join(output_dir, "subject01_walk1_ik.mot")
ik_tool.setOutputMotionFileName(os.path.abspath(ik_output))

# Set results directory so marker error files also go to output_dir
ik_tool.setResultsDir(os.path.abspath(output_dir))

# ------------------------------------------------
# Step 6: Run IK
# ------------------------------------------------

print("Running inverse kinematics...")
success = ik_tool.run()

if success:
    print(f"IK complete → {ik_output}")
else:
    print("IK failed")