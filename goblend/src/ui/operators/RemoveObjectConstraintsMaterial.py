import bpy

class SCENE_OT_RemoveObjectConstraintsMaterial(bpy.types.Operator):
    bl_idname = "scene.remove_object_constraints_material"
    bl_label = "Remove Material"
    bl_description = "Remove constraints for this material"

    def execute(self, context):
        obj = context.obj_for_mat_to_remove_for_constraints
        mat = context.mat_to_remove_for_constraints
        panels = None
        for i in range(len(context.scene.object_constraints_panel_props)):
            if context.scene.object_constraints_panel_props[i].obj == obj:
                panels = context.scene.object_constraints_panel_props[i].material_overrides
                break
        for i in range(len(panels)):
            if panels[i].mat == mat:
                panels.remove(i)
                break
        return {"FINISHED"}
