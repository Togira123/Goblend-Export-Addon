import bpy

class SCENE_OT_AddMaterialSetting(bpy.types.Operator):
    bl_idname = "scene.add_material_setting"
    bl_label = "Add Material Setting"
    bl_description = "Specify how a material should be handled"

    def execute(self, context):
        context.scene.material_panel_props.add()
        return {"FINISHED"}
