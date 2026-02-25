import bpy

class SCENE_OT_RemoveMaterialSetting(bpy.types.Operator):
    bl_idname = "scene.remove_material_setting"
    bl_label = "Remove Material"
    bl_description = "Remove constraints for this material"

    def execute(self, context):
        mat = context.material_setting_to_remove
        for i in range(len(context.scene.material_panel_props)):
            if context.scene.material_panel_props[i].mat == mat:
                context.scene.material_panel_props.remove(i)
                break
        return {"FINISHED"} 
