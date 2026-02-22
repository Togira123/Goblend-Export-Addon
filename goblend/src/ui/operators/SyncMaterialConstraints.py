import bpy

class SCENE_OT_SyncMaterialConstraints(bpy.types.Operator):
    bl_idname = "scene.sync_material_constraints"
    bl_label = "Sync Material Constraints"
    bl_description = "Make sure that every other object that also has this material has the same overriden settings"

    def execute(self, context):
        orig_obj = context.sync_original_obj
        mat = context.sync_mat

        scene = context.scene

        def is_valid_object(object):
            if object.type != "MESH":
                return False
            if object.library != None:
                return False
            collision_collection = bpy.data.collections.get("Collisions")
            if collision_collection and object.name in collision_collection.all_objects:
                return False
            has_mat = False
            for slot in object.material_slots:
                if slot.material == mat:
                    has_mat = True
                    break
            return has_mat
        
        constraint = None
        for c in scene.object_constraints_panel_props:
            if c.obj == orig_obj:
                constraint = c
                break
        
        mat_constraint = None
        for c in constraint.material_overrides:
            if c.mat == mat:
                mat_constraint = c
                break
        # get all objects
        all_objs = filter(is_valid_object, scene.collection.all_objects.values())
        for obj in all_objs:
            c = None
            for co in scene.object_constraints_panel_props:
                if co.obj == obj:
                    c = co
                    break
            if c == None:
                c = scene.object_constraints_panel_props.add() 
                c.obj = obj
            c.uv_map_enabled = True
            found_constraint = False
            for other_mat_c in c.material_overrides:
                if other_mat_c.mat == mat:
                    # constraint already, exists, make sure it uses the same settings
                    other_mat_c.use_shader = mat_constraint.use_shader
                    other_mat_c.override_quality = mat_constraint.override_quality
                    other_mat_c.texture_dim[0] = mat_constraint.texture_dim[0]
                    other_mat_c.texture_dim[1] = mat_constraint.texture_dim[1]
                    other_mat_c.transparency_mode = mat_constraint.transparency_mode
                    other_mat_c.transparency_alpha_scissor_threshold = mat_constraint.transparency_alpha_scissor_threshold
                    other_mat_c.cull_mode = mat_constraint.cull_mode
                    other_mat_c.uv_map_enabled = mat_constraint.uv_map_enabled
                    other_mat_c.uv_map_per_texture_enabled = mat_constraint.uv_map_per_texture_enabled
                    other_mat_c.uv_map = mat_constraint.uv_map
                    other_mat_c.uv_map_base_color = mat_constraint.uv_map_base_color
                    other_mat_c.uv_map_metallic_roughness = mat_constraint.uv_map_metallic_roughness
                    other_mat_c.uv_map_normal = mat_constraint.uv_map_normal
                    other_mat_c.limit_uv_effect_normal = mat_constraint.limit_uv_effect_normal 
                    other_mat_c.limit_uv_effect_normal_x_min = mat_constraint.limit_uv_effect_normal_x_min
                    other_mat_c.limit_uv_effect_normal_x_max = mat_constraint.limit_uv_effect_normal_x_max
                    other_mat_c.limit_uv_effect_normal_y_min = mat_constraint.limit_uv_effect_normal_y_min
                    other_mat_c.limit_uv_effect_normal_y_max = mat_constraint.limit_uv_effect_normal_y_max
                    found_constraint = True
                    break
            if not found_constraint:
                prop = c.material_overrides.add()
                prop.obj = obj
                prop.mat = mat
                prop.use_shader = mat_constraint.use_shader
                prop.override_quality = mat_constraint.override_quality
                prop.texture_dim[0] = mat_constraint.texture_dim[0]
                prop.texture_dim[1] = mat_constraint.texture_dim[1]
                prop.transparency_mode = mat_constraint.transparency_mode
                prop.transparency_alpha_scissor_threshold = mat_constraint.transparency_alpha_scissor_threshold
                prop.cull_mode = mat_constraint.cull_mode
                prop.uv_map_enabled = mat_constraint.uv_map_enabled
                prop.uv_map_per_texture_enabled = mat_constraint.uv_map_per_texture_enabled
                prop.uv_map = mat_constraint.uv_map
                prop.uv_map_base_color = mat_constraint.uv_map_base_color
                prop.uv_map_metallic_roughness = mat_constraint.uv_map_metallic_roughness
                prop.uv_map_normal = mat_constraint.uv_map_normal
                prop.limit_uv_effect_normal = mat_constraint.limit_uv_effect_normal 
                prop.limit_uv_effect_normal_x_min = mat_constraint.limit_uv_effect_normal_x_min
                prop.limit_uv_effect_normal_x_max = mat_constraint.limit_uv_effect_normal_x_max
                prop.limit_uv_effect_normal_y_min = mat_constraint.limit_uv_effect_normal_y_min
                prop.limit_uv_effect_normal_y_max = mat_constraint.limit_uv_effect_normal_y_max
        return {"FINISHED"}
