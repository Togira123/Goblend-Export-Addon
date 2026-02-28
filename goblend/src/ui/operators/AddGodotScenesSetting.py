import bpy


class SCENE_OT_AddGodotScenesSetting(bpy.types.Operator):
    bl_idname = "scene.add_godot_scene_setting"
    bl_label = "Add Godot Scene"
    bl_description = "Add an existing Godot Scene on import"

    def execute(self, context):
        context.scene.godot_scene_panel_props.add()
        return {"FINISHED"}
