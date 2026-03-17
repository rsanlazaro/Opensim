import opensim as osim
import os

# -----------------------------
# Input files
# -----------------------------

scaled_model_file = "results/scaling/scaled_model.osim"
ik_mot_file       = "results/ik/subject01_walk1_ik.mot"
grf_xml_file      = "./opensimFiles/Gait2354_Simbody/subject01_walk1_grf.xml"  # ← use XML directly

# -----------------------------
# Output directory
# -----------------------------

output_dir = "results/id"
os.makedirs(output_dir, exist_ok=True)

a = os.path.abspath

# ------------------------------------------------
# Step 1: Get time range from IK file
# ------------------------------------------------

ik_table   = osim.TimeSeriesTable(a(ik_mot_file))
start_time = ik_table.getIndependentColumn()[0]
end_time   = ik_table.getIndependentColumn()[-1]
print(f"Time range: {start_time:.3f}s → {end_time:.3f}s")

# ------------------------------------------------
# Step 2: Write ID setup XML
# ------------------------------------------------

setup_file = a(os.path.join(output_dir, "id_setup.xml"))
with open(setup_file, "w") as f:
    f.write(f"""<?xml version="1.0" encoding="UTF-8" ?>
<OpenSimDocument Version="40000">
    <InverseDynamicsTool name="id">
        <model_file>{a(scaled_model_file)}</model_file>
        <results_directory>{a(output_dir)}</results_directory>
        <output_precision>8</output_precision>
        <initial_time>{start_time}</initial_time>
        <final_time>{end_time}</final_time>
        <external_loads_file>{a(grf_xml_file)}</external_loads_file>
        <coordinates_file>{a(ik_mot_file)}</coordinates_file>
        <lowpass_cutoff_frequency_for_coordinates>6</lowpass_cutoff_frequency_for_coordinates>
        <output_gen_force_file>subject01_walk1_id.sto</output_gen_force_file>
    </InverseDynamicsTool>
</OpenSimDocument>
""")
print(f"Saved ID setup → {setup_file}")

# ------------------------------------------------
# Step 3: Run ID directly
# ------------------------------------------------

print("Running ID...")
try:
    id_tool = osim.InverseDynamicsTool(setup_file)
    success = id_tool.run()
    if success:
        print("ID complete")
    else:
        print("ID failed")
except Exception as e:
    print(f"ID exception: {e}")

print("Script finished")