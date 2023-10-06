# Initial Setup:
import arcpy
from arcpy import env
from arcpy.sa import *

# The Project's Geodatabase (GDB) File Path:
project_gdb = r"# Project's GDB's Path"

# List of SHP Files Needed To Be Imported To The Project's GDB:
import_shp_files_list = [r"# Path Of The Study Area's SHP File",
                         r"# Path Of The Original Cellular Tower Network's SHP File",
                         r"# Path Of The Cellular Tower Network With The Added Tower's SHP File"]
arcpy.conversion.FeatureClassToGeodatabase(import_shp_files_list, project_gdb)

# Import Study Area's DEM To The Project's GDB:
import_DEM = r"'# Path Of The Study Area's DEM'"
arcpy.conversion.RasterToGeodatabase(import_DEM, project_gdb, "")

# Set The Project's GDB As The Target Workspace For The Following Processes:
env.workspace = r"# Project's GDB's Path"

# Create A 30km Buffer For The Study Area:
in_feature = "# File Name Of The Study Area's Feature Class"
out_feature = "# File Name Of The Output 30km Buffer's Feature Class"
linear_distance = "30 Kilometers"
arcpy.analysis.Buffer(in_feature, out_feature, linear_distance, "FULL", "ROUND", "ALL", None, "PLANAR")

# Clip The Cellular Tower Network's Feature Class With The 30km Buffer Feature Class To Obtain All Towers Contributing To The Coverage Of LA County:
in_feature_to_be_clipped = "# File Name Of The Original Cellular Tower Network's Feature Class"
clip_feature = "# File Name Of The Output 30km Buffer's Feature Class"
out_feature_class = "# File Name Of The Output Cellular Tower Network's Feature Class With All Towers Within The Buffer"
arcpy.analysis.Clip(in_feature_to_be_clipped, clip_feature, out_feature_class)

# Create Copies Of The Output Cellular Tower Network's Feature Class With All Towers Within The Buffer With New File Name
# (These Copies Will Be Used For Field Calculation To Modify Their Parameter):
in_features_for_copying = "# File Name Of The Original Cellular Tower Network's Feature Class"
output_features_file_name_list = ["# File Name For Naming The Cellular Tower Network's Feature Class With Modified Height",
                                  "# File Name For Naming The Cellular Tower Network's Feature Class With Modified Radius"]
for name in output_features_file_name_list:
    arcpy.management.CopyFeatures(in_features_for_copying, name)
    print(f"\n{name} has been successfully created.")

# Perform Field Calculation To Modify The Parameters Of The Cellular Tower Network's Feature Class With Modified Height And Modified Radius:
modified_tower_list = ["# File Name For Naming The Cellular Tower Network's Feature Class With Modified Height",
                       "# File Name For Naming The Cellular Tower Network's Feature Class With Modified Radius"]
field_list = ["# Field's Name Of The Tower Height", "# Field's Name Of The Broadcasting Radius"]
expression_list = ["!# Field's Name Of The Tower Height! + 10", "!# Field's Name Of The Broadcasting Radius! + 5000"]
for tower, field, expression in zip(modified_tower_list, field_list, expression_list):
    arcpy.management.CalculateField(tower, field, expression, "PYTHON3")
    print(f"\n{field} in {tower} has been successfully modified.")

# Produce Visibility Raster For The 4 Tower Network Feature Classes (The Original, Modified Height, Modified Radius, New Network With Added Tower)
# To Identify Coverage With The "Visibility (Spatial Analyst)" Tool:
in_raster = "# File Name OF The Study Area's DEM "    # The input raster.
in_observer_features_list = ["# File Name Of The Original Cellular Tower Network's Feature Class",
                             "# File Name For The Cellular Tower Network's Feature Class With Modified Height",
                             "# File Name For The Cellular Tower Network's Feature Class With Modified Radius",
                             "# File Name For The Cellular Tower Network With The Added Tower"]
out_agl_raster = None   # Assign "None" To The Output Above-Ground-Level (AGL) Raster Since It's Not Needed.
analysis_type = "FREQUENCY"     # Assign "Frequency" As The Analysis Type Parameter.
nonvisible_cell_value = "ZERO"      # Assign "ZERO" as The Non-visible Cell Value Parameter. The Non-visible Cell In The Output Will Have A Value Of 0.
z_factor = 1    # Assign The Default Value Of 1 As The Z-Factor Parameter Since Unit Conversion Is Not Needed.
curvature_correction = "FLAT_EARTH"     # Assign "Flat Earth" (The Default) As The Curvature Correction Parameter.
refractivity_coefficient = 0.13     # Assign The Default Value Of 0.13 As The Refractivity Coefficient Parameter.
surface_offset = "# Field's Name For The Field Used As Surface Offset Parameter"      # Assign The Surface Offset Parameter.
observer_elevation = ""     # Assign An Empty String As The Observer Elevation Parameter.
observer_offset = "# Field's Name Of The Tower Height's Field"     # Assign The Value For The Observer Offset Parameter.
inner_radius = "# Field's Name For The Field Used As Inner Radius Parameter"        # Assign The Value For The Inner Radius Parameter.
outer_radius = "# Field's Name Of The Broadcasting Radius's Field"        # Assign The Value For The Outer Radius Parameter.
horizontal_start_angle = "# Field's Name For The Field Used As Horizontal Start Angle's Parameter"     # Assign The Value For The Horizontal Start Angle Parameter.
horizontal_end_angle = "# Field's Name For The Field Used As Horizontal End Angle's Parameter"       # Assign The Value For The Horizontal End Angle Parameter.
vertical_upper_angle = "# Field's Name For The Field Used As Vertical Upper Angle's Parameter"      # Assign The Value For The Vertical Upper Angle Parameter.
vertical_lower_angle = "# Field's Name For The Field Used As Vertical Lower Angle's Parameter"      # Assign The Value For The Vertical Lower Angle Parameter.
# A For Loop To Produce Visibility Raster (i.e., Coverage Raster) For Each Tower Network's Feature Class:
for observer in in_observer_features_list:
    out_vis = arcpy.sa.Visibility(in_raster, observer, out_agl_raster, analysis_type, nonvisible_cell_value, z_factor, curvature_correction,
           refractivity_coefficient, surface_offset, observer_elevation, observer_offset, inner_radius,
           outer_radius, horizontal_start_angle, horizontal_end_angle, vertical_upper_angle, vertical_lower_angle)
    out_vis.save(f"{observer}_Coverage")
    print(f"\n{observer}_Coverage has been successfully created.")

# Clip The 4 Output Visibility Raster With The Study Area's Feature Class To Produce Coverage Result Limited To land Only.
in_vis_ras_list = ["# File Name For The Visibility Raster Of The Original Tower Network",
                   "# File Name For The Visibility Raster Of The Tower Network With Modified Height",
                   "# File Name For The Visibility Raster Of The Tower Network With Modified Radius",
                   "# File Name For The Visibility Raster Of The Tower Network With Added Tower"]
in_mask_data = "# File Name For The Study Area's Feature Class"      # Assign The Input Mask Data.
extraction_area = "INSIDE"      # Assign "INSIDE" (The Default) As The Extraction Area Parameter.
# For Loop For Clipping The 4 Input Visibility Raster stored In The "in_vis_ras_list.":
for vis_ras in in_vis_ras_list:
    out_extract_ras = ExtractByMask(vis_ras, in_mask_data, extraction_area)
    out_extract_ras.save(f"{vis_ras}_limited")
    print(f"\n{vis_ras}_limited has been successfully created.")

# Add A New Text Field To Each Clipped Visibility Raster To Indicate Whether There Is Coverage Available or No coverage:
input_feature_list_for_field_calculation = ["# File Name Of The Clipped Visibility Raster For The Original Tower Network",
                                            "# File Name Of The Clipped Visibility Raster For The Tower Network With Modified Height",
                                            "# File Name Of The Clipped Visibility Raster For The Tower Network With Modified Radius",
                                            "# File Name Of The Clipped Visibility Raster For The Tower Network With Added Tower"]
new_field = "Coverage"  # Assign "Coverage" As The Name For The New Text Field.
field_type = "TEXT"
field_precision = ""
field_scale = ""
field_length = 30
field_alias = "Coverage Availability"   # Assign "Coverage Availability" As The Alias For The New Text Field.

# Code Block For Expression Used To Create The Result For The New Field:
# (If Input is 0, The New Field Value Will Be "No Coverage". Otherwise, It Will Be "Coverage Available".)
code_block = """
def Coverage_Identifier(v):
    if v == 0:
        C1 = "No Coverage"
        return C1
    else:
        C2 = "Coverage Available"
        return C2
"""
expression2 = "Coverage_Identifier(!Value!)"

# The For Loop For Creating A New Field For The 4 Clipped Visibility Raster And Calculating The Corresponding Field Value:
for input_features in input_feature_list_for_field_calculation:
    arcpy.management.AddField(input_features, new_field, field_type, field_precision, field_scale, field_length, field_alias)
    print(f"\nCoverage Field has been successfully added to {input_features}")
    arcpy.management.CalculateField(input_features, new_field, expression2, "PYTHON3", code_block)
    print(f"\nCoverage Availability has been successfully assigned to the Coverage Field in {input_features}")

print("\nProcess is completed!")