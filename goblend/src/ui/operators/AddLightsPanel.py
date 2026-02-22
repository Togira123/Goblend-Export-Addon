import bpy

class SCENE_OT_AddLightsPanel(bpy.types.Operator):
    bl_idname = "scene.add_lights_panel"
    bl_label = "Add Light Setting"
    bl_description = "Customize Light settings for import to Godot"

    def execute(self, context):
        context.scene.light_panel_props.add()
        return {"FINISHED"}
