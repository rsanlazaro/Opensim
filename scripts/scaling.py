import opensim as osim
import os

# -----------------------------
# Input files
# -----------------------------

model_file = "./opensimFiles/Gait2354_Simbody/gait2354_simbody.osim"
marker_set_file = "./opensimFiles/Gait2354_Simbody/gait2354_Scale_MarkerSet.xml"
static_trc = "./opensimFiles/Gait2354_Simbody/subject01_static.trc"

# -----------------------------
# Output directory
# -----------------------------

output_dir = "results/scaling"
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------------
# Step 1: Apply marker set and save to a temp model
# ------------------------------------------------

model = osim.Model(model_file)
model.initSystem()

marker_set = osim.MarkerSet(marker_set_file)
model.updateMarkerSet(marker_set)

temp_model_file = os.path.join(output_dir,"model_with_markers.osim")
model.printToXML(temp_model_file)
print(f"Saved model with {model.getMarkerSet().getSize()} markers to {temp_model_file}")

# ------------------------------------------------
# Step 2: Create scale tool pointing to temp model
# ------------------------------------------------

scale_tool = osim.ScaleTool()
scale_tool.setSubjectMass(75)
scale_tool.getGenericModelMaker().setModelFileName(temp_model_file)

# ------------------------------------------------
# Step 3: Apply static trial file (TRC) to the scaled model
# ------------------------------------------------

model_scaler = scale_tool.getModelScaler()
model_scaler.setMarkerFileName(static_trc)

time_range = osim.ArrayDouble()
time_range.append(0.5)
time_range.append(1.5)
model_scaler.setTimeRange(time_range)

# ------------------------------------------------
# Step 3: Apply static trial file (TRC) to place markers
# ------------------------------------------------

marker_placer = scale_tool.getMarkerPlacer()
marker_placer.setMarkerFileName(static_trc)
marker_placer.setOutputModelFileName(os.path.join(output_dir,"scaled_model.osim"))
marker_placer.setOutputMotionFileName(os.path.join(output_dir,"static_pose.mot"))
marker_placer.setTimeRange(time_range)

# ------------------------------------------------
# Step 4: Run scaling
# ------------------------------------------------

print("Running scaling...")
success = scale_tool.run()

if success:
    print("Scaling complete")
else:
    print("Scaling failed")