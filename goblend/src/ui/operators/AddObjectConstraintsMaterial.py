import bpy

class SCENE_OT_AddObjectConstraintsMaterial(bpy.types.Operator):
    bl_idname = "scene.add_object_constraints_material"
    bl_label = "Add Material"
    bl_description = "Add Material to apply object constraints to"

    def execute(self, context):
        obj = context.obj_to_add_material_to
        panels = None
        for i in range(len(context.scene.object_constraints_panel_props)):
            if context.scene.object_constraints_panel_props[i].obj == obj:
                panels = context.scene.object_constraints_panel_props[i].material_overrides
                break
        con = panels.add()
        con.obj = obj
        return {"FINISHED"}
