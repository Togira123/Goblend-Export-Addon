import bpy

class SCENE_OT_RemoveObjectSetting(bpy.types.Operator):
    bl_idname = "scene.remove_object_setting"
    bl_label = "Remove Object Constraint"
    bl_description = "Remove constraints for an object"

    def execute(self, context):
        obj = context.object_setting_to_remove
        for i in range(len(context.scene.object_panel_props)):
            if context.scene.object_panel_props[i].obj == obj:
                context.scene.object_panel_props.remove(i)
                break
        return {"FINISHED"}
