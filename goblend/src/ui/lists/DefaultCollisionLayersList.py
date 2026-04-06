# DefaultCollisionLayersList.py
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
from .CollisionLayersList import layer_items


class DefaultCollisionLayerListItem(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enable", description="Enable or disable this layer", default=True)
    force_disabled: bpy.props.BoolProperty(
        name="Force Disabled", description="There exists another entry for this layer already", default=False
    )
    layer: bpy.props.EnumProperty(
        name="Layer",
        items=layer_items,
    )


class SCENE_UL_DefaultCollisionLayersList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
        for i in range(index):
            if data.default_layers_list[i].layer == item.layer:
                # another one before has the same prop, disable
                duplicate = True
                break
        col1.enabled = not duplicate
        if duplicate:
            col1.prop(item, "force_disabled", text="")
        else:
            col1.prop(item, "enabled", text="")
        col1.alignment = "RIGHT"
        col2 = row.row()
        col2.enabled = item.enabled
        col2.prop(item, "layer", text="")


class LIST_OT_AddItemToDefaultLayersList(bpy.types.Operator):
    bl_idname = "default_collision_layers_list.add_item"
    bl_label = "Add a layer"

    @classmethod
    def poll(cls, context):
        return len(context.scene.default_collision_panel_props.default_layers_list) < len(layer_items(cls, context))

    def execute(self, context):
        # find first unused layer
        existing = set()
        for override in context.scene.default_collision_panel_props.default_layers_list:
            existing.add(override.layer)
        item = context.scene.default_collision_panel_props.default_layers_list.add()
        all_layers = layer_items(self, context)
        for layer in all_layers:
            if not layer[0] in existing:
                item.layer = layer[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromDefaultLayersList(bpy.types.Operator):
    bl_idname = "default_collision_layers_list.remove_item"
    bl_label = "Remove a layer"

    @classmethod
    def poll(cls, context):
        return context.scene.default_collision_panel_props.default_layers_list

    def execute(self, context):
        li = context.scene.default_collision_panel_props.default_layers_list
        index = context.scene.default_collision_panel_props.default_layers_list_index
        li.remove(index)
        context.scene.default_collision_panel_props.default_layers_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
