import bpy


class SCENE_PT_ObjectsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Objects"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        object_panel_props = scene.object_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in object_panel_props:
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
            row.context_pointer_set(name="object_setting_to_remove", data=item.obj)
            row.operator("scene.remove_object_setting", text="", icon="X", emboss=False)

            # panel body
            if panel:
                panel.use_property_split = True
                panel.enabled = item.enabled
                col = panel.column()
                col.prop(item, "obj")
                col.prop(item, "uv_map_enabled")
                if item.uv_map_enabled:
                    col.prop(item, "uv_map_per_texture_enabled")
                    if item.uv_map_per_texture_enabled:
                        col.prop(item, "uv_map_base_color")
                        col.prop(item, "uv_map_metallic_roughness")
                        col.prop(item, "uv_map_normal")
                    else:
                        col.prop(item, "uv_map")
                col.prop(item, "shadow_cast_mode")
