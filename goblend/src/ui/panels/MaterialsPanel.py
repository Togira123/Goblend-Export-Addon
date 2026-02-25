import bpy

class SCENE_PT_MaterialsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Materials"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        material_panel_props = scene.material_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for mat in material_panel_props:
            header, panel = layout.panel_prop(mat, "open")
            # panel header
            split = header.split()

            col = split.column()
            mat_name = mat.mat.name if mat.mat else "No Material"
            col.label(text=mat_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="material_setting_to_remove", data=mat.mat)
            row.operator("scene.remove_material_setting", text="", icon="X", emboss=False)

            if panel:
                col = panel.column()
                col.prop(mat, "mat")
                col.prop(mat, "transparency_mode")
                if mat.transparency_mode == "SCISSOR":
                    col.prop(mat, "transparency_alpha_scissor_threshold")
                col.prop(mat, "cull_mode")
                if mat.use_shader:
                    col2 = col.column()
                    col2.enabled = False
                    col2.prop(mat, "force_texture_group_disabled")
                    col2.prop(mat, "force_override_bake_margin_disabled")
                else:
                    col.prop(mat, "texture_group")
                    col.prop(mat, "override_bake_margin")
                    if mat.override_bake_margin:
                        col.prop(mat, "bake_margin")
                col.prop(mat, "override_quality")
                if mat.override_quality:
                    col.prop(mat, "texture_dim")
                col.prop(mat, "use_shader")
                col.prop(mat, "limit_uv_effect_normal")
                if mat.limit_uv_effect_normal:
                    col.prop(mat, "limit_uv_effect_normal_x_min")
                    col.prop(mat, "limit_uv_effect_normal_x_max")
                    col.prop(mat, "limit_uv_effect_normal_y_min")
                    col.prop(mat, "limit_uv_effect_normal_y_max")
