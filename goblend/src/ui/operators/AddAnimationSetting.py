import bpy


class SCENE_OT_AddAnimationSetting(bpy.types.Operator):
    bl_idname = "scene.add_animation_setting"
    bl_label = "Add Animation Setting"
    bl_description = "Customize Animation settings for Godot"

    def execute(self, context):
        context.scene.animation_panel_props.add()
        return {"FINISHED"}
