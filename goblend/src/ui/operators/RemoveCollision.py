import bpy

class SCENE_OT_RemoveCollision(bpy.types.Operator):
    bl_idname = "scene.remove_collision"
    bl_label = "Remove Collision"
    bl_description = "Remove the collision settings for a collision collection"

    def execute(self, context):
        collection = context.collision_collection_to_delete
        for i in range(len(context.scene.collision_panel_props)):
            if context.scene.collision_panel_props[i].collection == collection:
                context.scene.collision_panel_props.remove(i)
                break
        return {"FINISHED"}
