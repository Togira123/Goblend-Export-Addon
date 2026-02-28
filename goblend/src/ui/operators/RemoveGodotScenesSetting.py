import bpy


class SCENE_OT_RemoveGodotScenesSetting(bpy.types.Operator):
    bl_idname = "scene.remove_godot_scene_setting"
    bl_label = "Remove Godot Scene"
    bl_description = "Remove Godot scene"

    def execute(self, context):
        obj = context.godot_scene_to_remove
        for i in range(len(context.scene.godot_scene_panel_props)):
            if context.scene.godot_scene_panel_props[i].obj == obj:
                context.scene.godot_scene_panel_props.remove(i)
                break
        return {"FINISHED"}
