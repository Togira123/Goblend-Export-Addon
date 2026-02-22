import bpy

class SCENE_OT_RemoveAnimationPanel(bpy.types.Operator):
    bl_idname = "scene.remove_animation"
    bl_label = "Remove Animation Setting"
    bl_description = "Remove the animation setting for this animation"

    def execute(self, context):
        animation = context.animation_to_delete
        for i in range(len(context.scene.animations_panel_props)):
            if context.scene.animations_panel_props[i].animation == animation:
                context.scene.animations_panel_props.remove(i)
                break
        return {"FINISHED"}
