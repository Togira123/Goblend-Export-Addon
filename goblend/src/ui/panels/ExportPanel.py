import bpy

class SCENE_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Export to Godot"
    bl_idname = "SCENE_PT_export_to_godot"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        panel_props = scene.panel_props

        default_collision_panel_props = scene.default_collision_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        # global properties
        col = layout.column()

        paths_header, paths_panel = col.panel_prop(panel_props, "open_paths_panel")
        paths_header.label(text="Save Paths")
        if paths_panel:
            paths_panel_col = paths_panel.column()
            paths_panel_col.prop(panel_props, "same_hierarchy_target")
            paths_panel_col.prop(panel_props, "scene_save_path")
            paths_panel_col.prop(panel_props, "scene_use_same_hierarchy")
            paths_panel_col.prop(panel_props, "material_save_path")
            paths_panel_col.prop(panel_props, "material_use_same_hierarchy")
            paths_panel_col.prop(panel_props, "texture_save_path")
            paths_panel_col.prop(panel_props, "texture_use_same_hierarchy")
            paths_panel_col.prop(panel_props, "animation_library_save_path")
            paths_panel_col.prop(panel_props, "animation_library_use_same_hierarchy")
            paths_panel_col.prop(panel_props, "animation_save_path")
            paths_panel_col.prop(panel_props, "animation_use_same_hierarchy")
            paths_panel_col.prop(panel_props, "shader_save_path")
            paths_panel_col.prop(panel_props, "shader_use_same_hierarchy")
            paths_panel_col.prop(panel_props, "collision_shapes_save_path")
            paths_panel_col.prop(panel_props, "reuse_collision_shapes")

        col.label(text="Texture Dimensions")
        col.prop(panel_props, "texture_dim", text="")
        
        col.prop(panel_props, "transparency_mode")
        if panel_props.transparency_mode == "SCISSOR":
            col.prop(panel_props, "transparency_alpha_scissor_threshold")
        
        col.prop(panel_props, "cull_mode")

        col.separator()

        col.prop(default_collision_panel_props, "type")

        default_layers_header, default_layers_panel = col.panel_prop(default_collision_panel_props, "default_layers_panel_open")
        default_layers_header.label(text="Default Collision Layers")
        if default_layers_panel:
            inner_col = default_layers_panel.column()
            inner_col.prop(default_collision_panel_props, "use_layer_config_value")
            row = default_layers_panel.row()
            row.template_list("SCENE_UL_DefaultCollisionLayersList", "default_layers_list", default_collision_panel_props, "default_layers_list", default_collision_panel_props, "default_layers_list_index")
            
            if default_collision_panel_props.use_layer_config_value:
                row.enabled = False

            inner_col = row.column(align=True)
            inner_col.operator("default_collision_layers_list.add_item", icon="ADD", text="")
            inner_col.operator("default_collision_layers_list.remove_item", icon="REMOVE", text="")

        default_masks_header, default_masks_panel = col.panel_prop(default_collision_panel_props, "default_masks_panel_open")
        default_masks_header.label(text="Default Collision Masks")
        if default_masks_panel:
            inner_col = default_masks_panel.column()
            inner_col.prop(default_collision_panel_props, "use_mask_config_value")
            row = default_masks_panel.row()
            row.template_list("SCENE_UL_DefaultCollisionMasksList", "default_masks_list", default_collision_panel_props, "default_masks_list", default_collision_panel_props, "default_masks_list_index")

            if default_collision_panel_props.use_mask_config_value:
                row.enabled = False


            inner_col = row.column(align=True)
            inner_col.operator("default_collision_masks_list.add_item", icon="ADD", text="")
            inner_col.operator("default_collision_masks_list.remove_item", icon="REMOVE", text="")
        
        default_groups_header, default_groups_panel = col.panel_prop(default_collision_panel_props, "default_groups_panel_open")
        default_groups_header.label(text="Default Groups")
        if default_groups_panel:
            row = default_groups_panel.row()
            row.template_list("SCENE_UL_DefaultGroupList", "default_group_list", default_collision_panel_props, "default_groups_list", default_collision_panel_props, "default_groups_list_index")

            inner_col = row.column(align=True)
            inner_col.operator("default_group_list.add_item", icon="ADD", text="")
            inner_col.operator("default_group_list.remove_item", icon="REMOVE", text="")

        layout.separator()

        # export button
        layout.operator("scene.root_export_to_godot", icon="RENDER_STILL")

        # add object constraints
        layout.operator("scene.add_object_constraints", icon="ADD")
        
        layout.operator("scene.add_collision_panel", icon="ADD")
        
        layout.operator("scene.add_animation_panel", icon="ADD")

        layout.operator("scene.add_godot_scene_panel", icon="ADD")

        layout.operator("scene.add_lights_panel", icon="ADD")
