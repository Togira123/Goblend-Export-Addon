# AnimationsPanel.py
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


class SCENE_PT_AnimationsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Animations"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        animation_panel_props = scene.animation_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in animation_panel_props:
            header, panel = layout.panel_prop(item, "open")

            split = header.split()

            col = split.column()

            animation_name = item.animation.name if item.animation else "No Animation"

            col.label(text=animation_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="animation_to_remove", data=item.animation)
            row.operator("scene.remove_animation_setting", text="", icon="X", emboss=False)

            if panel:
                panel.use_property_split = True
                col = panel.column()
                col.prop(item, "animation")
                col.prop(item, "loop")
                col.prop(item, "autoplay")
