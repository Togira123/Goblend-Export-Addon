import bpy

class SCENE_OT_RemoveGodotScenesPanel(bpy.types.Operator):
    bl_idname = "scene.remove_godot_scene"
    bl_label = "Remove Godot Scene"
    bl_description = "Remove Godot scene"

    def execute(self, context):
        obj = context.godot_scene_to_delete
        for i in range(len(context.scene.godot_scene_panel_props)):
            if context.scene.godot_scene_panel_props[i].obj == obj:
                context.scene.godot_scene_panel_props.remove(i)
                break
        return {"FINISHED"}
