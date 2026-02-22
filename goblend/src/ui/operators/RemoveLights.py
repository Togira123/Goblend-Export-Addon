import bpy

class SCENE_OT_RemoveLight(bpy.types.Operator):
    bl_idname = "scene.remove_light"
    bl_label = "Remove Light Setting"
    bl_description = "Remove this light setting"

    def execute(self, context):
        light = context.light_to_delete
        for i in range(len(context.scene.light_panel_props)):
            if context.scene.light_panel_props[i].light == light:
                context.scene.light_panel_props.remove(i)
                break
        return {"FINISHED"}
