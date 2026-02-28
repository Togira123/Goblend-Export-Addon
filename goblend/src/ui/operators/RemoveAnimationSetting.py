import bpy


class SCENE_OT_RemoveAnimationSetting(bpy.types.Operator):
    bl_idname = "scene.remove_animation_setting"
    bl_label = "Remove Animation Setting"
    bl_description = "Remove the animation setting for this animation"

    def execute(self, context):
        animation = context.animation_to_remove
        for i in range(len(context.scene.animation_panel_props)):
            if context.scene.animation_panel_props[i].animation == animation:
                context.scene.animation_panel_props.remove(i)
                break
        return {"FINISHED"}
