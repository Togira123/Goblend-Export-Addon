import bpy

class SCENE_OT_AddObjectConstraints(bpy.types.Operator):
    bl_idname = "scene.add_object_constraints"
    bl_label = "Add Object Constraints"
    bl_description = "Customize settings for individual objects"

    def execute(self, context):
        context.scene.object_constraints_panel_props.add() 
        return {"FINISHED"}
