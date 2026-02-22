import bpy

class SCENE_OT_AddAnimationPanel(bpy.types.Operator):
    bl_idname = "scene.add_animation_panel"
    bl_label = "Add Animation Setting"
    bl_description = "Customize Animation settings for Godot"

    def execute(self, context):
        context.scene.animations_panel_props.add()
        return {"FINISHED"}
