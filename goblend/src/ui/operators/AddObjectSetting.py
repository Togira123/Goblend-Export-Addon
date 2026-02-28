import bpy


class SCENE_OT_AddObjectSetting(bpy.types.Operator):
    bl_idname = "scene.add_object_setting"
    bl_label = "Add Object Setting"
    bl_description = "Customize settings for individual objects"

    def execute(self, context):
        context.scene.object_panel_props.add()
        return {"FINISHED"}
