# LightsPanel.py
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


class SCENE_PT_LightsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Lights"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        light_panel_props = scene.light_panel_props
        show_all_light_settings = scene.show_all_light_settings

        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(scene, "show_all_light_settings")
        layout.operator("scene.sync_lights", icon="IMPORT")

        for item in light_panel_props:
            header, panel = layout.panel_prop(item, "open")

            split = header.split()

            col = split.column()

            light_name = item.light.name if item.light else "No Light"

            col.label(text=light_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="light_setting_to_remove", data=item.light)
            row.operator("scene.remove_light_setting", text="", icon="X", emboss=False)

            if panel:
                panel.use_property_split = True
                col = panel.column()
                col.prop(item, "light")
                col.prop(item, "type")
                if item.type == "OmniLight3D":
                    col2 = panel.column()
                    col2.prop(item, "omni_range")
                    col2.prop(item, "omni_attenuation")
                    col2.prop(item, "omni_shadow_mode")
                elif item.type == "SpotLight3D":
                    col2 = panel.column()
                    col2.prop(item, "spot_range")
                    col2.prop(item, "spot_attenuation")
                    col2.prop(item, "spot_angle")
                    col2.prop(item, "spot_angle_attenuation")
                col = panel.column()
                col.prop(item, "light_color")
                col.prop(item, "light_energy")
                if show_all_light_settings:
                    col.prop(item, "light_indirect_energy")
                    col.prop(item, "light_volumetric_fog_energy")
                    col.prop(item, "light_angular_distance")
                    col.prop(item, "light_size")
                    col.prop(item, "light_negative")
                    col.prop(item, "light_specular")
                    col.prop(item, "light_bake_mode")
                    col.prop(item, "light_cull_mask")
                    col.prop(item, "shadow_enabled")
