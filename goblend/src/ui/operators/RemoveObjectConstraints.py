import bpy

class SCENE_OT_RemoveObjectConstraints(bpy.types.Operator):
    bl_idname = "scene.remove_object_constraints"
    bl_label = "Remove Object Constraint"
    bl_description = "Remove constraints for an object"

    def execute(self, context):
        obj = context.object_constraints_to_remove
        for i in range(len(context.scene.object_constraints_panel_props)):
            if context.scene.object_constraints_panel_props[i].obj == obj:
                context.scene.object_constraints_panel_props.remove(i)
                break
        return {"FINISHED"}
