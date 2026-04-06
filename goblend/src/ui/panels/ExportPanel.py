# ExportPanel.py
#
# Copyright (C) 2026-present Goblend contributers, see https://github.com/Togira123/Goblend-Export-Addon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>


import bpy


class SCENE_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Goblend: Export to Godot"
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
            scene_paths_header, scene_paths_panel = paths_panel_col.panel_prop(panel_props, "open_scene_path_panel")
            scene_paths_header.label(text="Scene Save Path")
            if scene_paths_panel:
                scene_paths_panel_col = scene_paths_panel.column()
                scene_paths_panel_col.prop(panel_props, "scene_save_path")
                scene_paths_panel_col.prop(panel_props, "scene_use_same_hierarchy")

            material_paths_header, material_paths_panel = paths_panel_col.panel_prop(
                panel_props, "open_material_path_panel"
            )
            material_paths_header.label(text="Material Save Path")
            if material_paths_panel:
                material_paths_panel_col = material_paths_panel.column()
                material_paths_panel_col.prop(panel_props, "save_material_separately")
                material_paths_panel_col.prop(panel_props, "material_save_path")
                material_paths_panel_col.prop(panel_props, "material_use_same_hierarchy")

            texture_paths_header, texture_paths_panel = paths_panel_col.panel_prop(
                panel_props, "open_texture_path_panel"
            )
            texture_paths_header.label(text="Texture Save Path")
            if texture_paths_panel:
                texture_paths_panel_col = texture_paths_panel.column()
                texture_paths_panel_col.prop(panel_props, "texture_save_path")
                texture_paths_panel_col.prop(panel_props, "texture_use_same_hierarchy")

            animation_library_paths_header, animation_library_paths_panel = paths_panel_col.panel_prop(
                panel_props, "open_animation_library_path_panel"
            )
            animation_library_paths_header.label(text="Animation Library Save Path")
            if animation_library_paths_panel:
                animation_library_paths_panel_col = animation_library_paths_panel.column()
                animation_library_paths_panel_col.prop(panel_props, "save_animation_library_separately")
                animation_library_paths_panel_col.prop(panel_props, "animation_library_save_path")
                animation_library_paths_panel_col.prop(panel_props, "animation_library_use_same_hierarchy")

            animation_paths_header, animation_paths_panel = paths_panel_col.panel_prop(
                panel_props, "open_animation_path_panel"
            )
            animation_paths_header.label(text="Animation Save Path")
            if animation_paths_panel:
                animation_paths_panel_col = animation_paths_panel.column()
                animation_paths_panel_col.prop(panel_props, "save_animation_separately")
                animation_paths_panel_col.prop(panel_props, "animation_save_path")
                animation_paths_panel_col.prop(panel_props, "animation_use_same_hierarchy")

            shader_paths_header, shader_paths_panel = paths_panel_col.panel_prop(panel_props, "open_shader_path_panel")
            shader_paths_header.label(text="Shader Save Path")
            if shader_paths_panel:
                shader_paths_panel_col = shader_paths_panel.column()
                shader_paths_panel_col.prop(panel_props, "save_shader_separately")
                shader_paths_panel_col.prop(panel_props, "shader_save_path")
                shader_paths_panel_col.prop(panel_props, "shader_use_same_hierarchy")

            collision_shapes_paths_header, collision_shapes_paths_panel = paths_panel_col.panel_prop(
                panel_props, "open_collision_shapes_path_panel"
            )
            collision_shapes_paths_header.label(text="Collision Shape Save Path")
            if collision_shapes_paths_panel:
                collision_shapes_paths_panel_col = collision_shapes_paths_panel.column()
                collision_shapes_paths_panel_col.prop(panel_props, "collision_shapes_save_path")
                collision_shapes_paths_panel_col.prop(panel_props, "reuse_collision_shapes")

            mesh_paths_header, mesh_paths_panel = paths_panel_col.panel_prop(panel_props, "open_mesh_path_panel")
            mesh_paths_header.label(text="Mesh Save Path")
            if mesh_paths_panel:
                mesh_paths_panel_col = mesh_paths_panel.column()
                mesh_paths_panel_col.prop(panel_props, "save_mesh_separately")
                mesh_paths_panel_col.prop(panel_props, "mesh_save_path")
                mesh_paths_panel_col.prop(panel_props, "mesh_use_same_hierarchy")

        col.label(text="Texture Dimensions")
        col.prop(panel_props, "texture_dim", text="")

        col.prop(panel_props, "default_transparency_mode")
        if panel_props.default_transparency_mode == "SCISSOR":
            col.prop(panel_props, "default_transparency_alpha_scissor_threshold")

        col.prop(panel_props, "default_cull_mode")

        col.separator()

        col.prop(default_collision_panel_props, "type")

        default_layers_header, default_layers_panel = col.panel_prop(
            default_collision_panel_props, "default_layers_panel_open"
        )
        default_layers_header.label(text="Default Collision Layers")
        if default_layers_panel:
            inner_col = default_layers_panel.column()
            inner_col.prop(default_collision_panel_props, "use_layer_config_value")
            row = default_layers_panel.row()
            row.template_list(
                "SCENE_UL_DefaultCollisionLayersList",
                "default_layers_list",
                default_collision_panel_props,
                "default_layers_list",
                default_collision_panel_props,
                "default_layers_list_index",
            )

            if default_collision_panel_props.use_layer_config_value:
                row.enabled = False

            inner_col = row.column(align=True)
            inner_col.operator("default_collision_layers_list.add_item", icon="ADD", text="")
            inner_col.operator("default_collision_layers_list.remove_item", icon="REMOVE", text="")

        default_masks_header, default_masks_panel = col.panel_prop(
            default_collision_panel_props, "default_masks_panel_open"
        )
        default_masks_header.label(text="Default Collision Masks")
        if default_masks_panel:
            inner_col = default_masks_panel.column()
            inner_col.prop(default_collision_panel_props, "use_mask_config_value")
            row = default_masks_panel.row()
            row.template_list(
                "SCENE_UL_DefaultCollisionMasksList",
                "default_masks_list",
                default_collision_panel_props,
                "default_masks_list",
                default_collision_panel_props,
                "default_masks_list_index",
            )

            if default_collision_panel_props.use_mask_config_value:
                row.enabled = False

            inner_col = row.column(align=True)
            inner_col.operator("default_collision_masks_list.add_item", icon="ADD", text="")
            inner_col.operator("default_collision_masks_list.remove_item", icon="REMOVE", text="")

        default_groups_header, default_groups_panel = col.panel_prop(
            default_collision_panel_props, "default_groups_panel_open"
        )
        default_groups_header.label(text="Default Groups")
        if default_groups_panel:
            row = default_groups_panel.row()
            row.template_list(
                "SCENE_UL_DefaultGroupList",
                "default_group_list",
                default_collision_panel_props,
                "default_groups_list",
                default_collision_panel_props,
                "default_groups_list_index",
            )

            inner_col = row.column(align=True)
            inner_col.operator("default_group_list.add_item", icon="ADD", text="")
            inner_col.operator("default_group_list.remove_item", icon="REMOVE", text="")

        layout.separator()

        # export button
        layout.operator("scene.root_export_to_godot", icon="RENDER_STILL")

        # add object constraints
        layout.operator("scene.add_object_setting", icon="ADD")

        layout.operator("scene.add_material_setting", icon="ADD")

        layout.operator("scene.add_collision_setting", icon="ADD")

        layout.operator("scene.add_animation_setting", icon="ADD")

        layout.operator("scene.add_godot_scene_setting", icon="ADD")

        layout.operator("scene.add_lights_setting", icon="ADD")
