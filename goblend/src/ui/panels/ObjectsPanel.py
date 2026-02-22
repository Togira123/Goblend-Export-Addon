import bpy

# orig_obj is object to take the override from and apply to others
# check whether the settings for this object and material are the same as for all the other objects
def mat_is_synced(mat, orig_obj):
    if mat == None or orig_obj == None:
        return True
    scene = bpy.context.scene
    constraint = None
    for c in scene.object_constraints_panel_props:
        if c.obj == orig_obj:
            constraint = c
            break
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
            return False
        found_constraint = False
        for other_mat_c in c.material_overrides:
            if other_mat_c.mat == mat:
                # check whether they are the same settings
                if mat_constraint.use_shader != other_mat_c.use_shader:
                    return False
                if mat_constraint.override_quality != other_mat_c.override_quality:
                    return False
                if mat_constraint.texture_dim[0] != other_mat_c.texture_dim[0]:
                    return False
                if mat_constraint.texture_dim[1] != other_mat_c.texture_dim[1]:
                    return False
                if mat_constraint.transparency_mode != other_mat_c.transparency_mode:
                    return False
                if mat_constraint.transparency_alpha_scissor_threshold != other_mat_c.transparency_alpha_scissor_threshold:
                    return False
                if mat_constraint.cull_mode != other_mat_c.cull_mode:
                    return False
                if mat_constraint.uv_map_enabled != other_mat_c.uv_map_enabled:
                    return False
                if mat_constraint.uv_map_per_texture_enabled != other_mat_c.uv_map_per_texture_enabled:
                    return False
                if mat_constraint.uv_map != other_mat_c.uv_map:
                    return False
                if mat_constraint.uv_map_base_color != other_mat_c.uv_map_base_color:
                    return False
                if mat_constraint.uv_map_metallic_roughness != other_mat_c.uv_map_metallic_roughness:
                    return False
                if mat_constraint.uv_map_normal != other_mat_c.uv_map_normal:
                    return False
                if mat_constraint.limit_uv_effect_normal != other_mat_c.limit_uv_effect_normal:
                    return False
                if mat_constraint.limit_uv_effect_normal_x_min != other_mat_c.limit_uv_effect_normal_x_min:
                    return False
                if mat_constraint.limit_uv_effect_normal_x_max != other_mat_c.limit_uv_effect_normal_x_max:
                    return False
                if mat_constraint.limit_uv_effect_normal_y_min != other_mat_c.limit_uv_effect_normal_y_min:
                    return False
                if mat_constraint.limit_uv_effect_normal_y_max != other_mat_c.limit_uv_effect_normal_y_max:
                    return False
                found_constraint = True
                break
        if not found_constraint:
            return False
    return True

class SCENE_PT_ObjectsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Objects"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        object_constraints_panel_props = scene.object_constraints_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in object_constraints_panel_props:
            header, panel = layout.panel_prop(item, "open")

            # panel header
            split = header.split()

            col = split.column()
            obj_name = item.obj.name if item.obj else "No Object"
            col.label(text=obj_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.prop(item, "enabled", text="")
            row.separator(factor=3.0, type="SPACE")
            row.context_pointer_set(name="object_constraints_to_remove", data=item.obj)
            row.operator("scene.remove_object_constraints", text="", icon="X", emboss=False)

            # panel body
            if panel:
                panel.use_property_split = True
                panel.enabled = item.enabled
                col = panel.column()
                col.prop(item, "obj")
                col.prop(item, "uv_group")
                col.prop(item, "shadow_cast_mode")
                
                col.context_pointer_set(name="obj_to_add_material_to", data=item.obj)
                col2 = col.column()
                if not item.obj:
                    col2.enabled = False
                col2.operator("scene.add_object_constraints_material", icon="ADD")
                for mat in item.material_overrides:
                    subheader, subpanel = panel.panel_prop(mat, "open")

                    # subpanel header
                    split = subheader.split()

                    col = split.column()
                    mat_name = mat.mat.name if mat.mat else "No Material"
                    col.label(text=mat_name)

                    row = split.row()
                    row.alignment = "RIGHT"
                    row.context_pointer_set(name="obj_for_mat_to_remove_for_constraints", data=item.obj)
                    row.context_pointer_set(name="mat_to_remove_for_constraints", data=mat.mat)
                    row.operator("scene.remove_object_constraints_material", text="", icon="X", emboss=False)

                    if subpanel:
                        if not item.obj:
                            subpanel.enabled = False
                        col = subpanel.column()
                        col.prop(mat, "mat")
                        if not mat_is_synced(mat.mat, item.obj):
                            col.context_pointer_set(name="sync_original_obj", data=item.obj)
                            col.context_pointer_set(name="sync_mat", data=mat.mat)
                            col.operator("scene.sync_material_constraints", icon="WARNING_LARGE")
                        col.prop(mat, "transparency_mode")
                        if mat.transparency_mode == "SCISSOR":
                            col.prop(mat, "transparency_alpha_scissor_threshold")
                        col.prop(mat, "cull_mode")
                        col.prop(mat, "override_quality")
                        if mat.override_quality:
                            col.prop(mat, "texture_dim")
                        col.prop(mat, "use_shader")
                        if mat.use_shader:
                            col2 = col.column()
                            col2.prop(mat, "force_uv_map_disabled")
                            col2.enabled = False
                        else:
                            col.prop(mat, "uv_map_enabled")
                        if mat.uv_map_enabled and not mat.use_shader:
                            col.prop(mat, "uv_map_per_texture_enabled")
                            if mat.uv_map_per_texture_enabled:
                                col.prop(mat, "uv_map_base_color")
                                col.prop(mat, "uv_map_metallic_roughness")
                                col.prop(mat, "uv_map_normal")
                            else:
                                col.prop(mat, "uv_map")
                        col.prop(mat, "limit_uv_effect_normal")
                        if mat.limit_uv_effect_normal:
                            col.prop(mat, "limit_uv_effect_normal_x_min")
                            col.prop(mat, "limit_uv_effect_normal_x_max")
                            col.prop(mat, "limit_uv_effect_normal_y_min")
                            col.prop(mat, "limit_uv_effect_normal_y_max")
