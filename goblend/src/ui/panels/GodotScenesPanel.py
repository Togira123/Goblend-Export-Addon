# GodotScenesPanel.py
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


class SCENE_PT_GodotScenesPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Godot Scenes"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        godot_scene_panel_props = scene.godot_scene_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in godot_scene_panel_props:
            header, panel = layout.panel_prop(item, "open")

            split = header.split()

            col = split.column()

            obj_name = item.obj.name if item.obj else "No Object"

            col.label(text=obj_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="godot_scene_to_remove", data=item.obj)
            row.operator("scene.remove_godot_scene_setting", text="", icon="X", emboss=False)

            if panel:
                panel.use_property_split = True
                col = panel.column()
                col.prop(item, "obj")
                col.prop(item, "scene")
