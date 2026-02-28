import bpy
from ... import __package__ as base_package


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = base_package

    godot_file_path: bpy.props.StringProperty(
        name="Godot Executable", description="Choose the Godot Executable", subtype="FILE_PATH"
    )
    create_log_file: bpy.props.BoolProperty(
        name="Create Log File",
        description="If this is checked, each export will write its log to a log file created in the root of your project.",
        default=True,
    )

    def draw(self, context):
        self.layout.prop(self, "godot_file_path")
        self.layout.prop(self, "create_log_file")
