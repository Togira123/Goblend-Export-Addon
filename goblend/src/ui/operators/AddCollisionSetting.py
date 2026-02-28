import bpy


class SCENE_OT_AddCollisionSetting(bpy.types.Operator):
    bl_idname = "scene.add_collision_setting"
    bl_label = "Add Collision Setting"
    bl_description = "Customize collision settings for different collision collections"

    def execute(self, context):
        context.scene.collision_panel_props.add()
        return {"FINISHED"}
