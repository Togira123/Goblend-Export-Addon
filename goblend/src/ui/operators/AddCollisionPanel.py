import bpy

class SCENE_OT_AddCollisionPanel(bpy.types.Operator):
    bl_idname = "scene.add_collision_panel"
    bl_label = "Add Collision Setting"
    bl_description = "Customize collision settings for different collision collections"

    def execute(self, context):
        context.scene.collision_panel_props.add()
        return {"FINISHED"}
