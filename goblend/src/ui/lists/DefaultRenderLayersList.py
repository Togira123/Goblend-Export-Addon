# DefaultRenderLayersList.py
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

from typing import cast, TYPE_CHECKING

from ...types.goblend_types import GoblendContext, OperatorReturnItems
from .RenderLayersList import layer_items

if TYPE_CHECKING:
    from ..property_groups.PanelProperties import PanelProperties

from ...types.property_types import typed_prop_group, BoolProp, EnumProp


@typed_prop_group
class DefaultRenderLayerListItem(bpy.types.PropertyGroup):
    enabled = BoolProp(name="Enable", description="Enable or disable this layer", default=True)
    force_disabled = BoolProp(
        name="Force Disabled", description="There exists another entry for this layer already", default=False
    )
    layer = EnumProp(
        name="Layer",
        items=layer_items,
    )


class SCENE_UL_DefaultRenderLayersList(bpy.types.UIList):
    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: "PanelProperties | None",
        item: DefaultRenderLayerListItem | None,
        icon: int | None,
        active_data: "PanelProperties",
        active_property: str | None,
        index: int | None,
        flt_flag: int | None,
    ) -> None:
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
        if not data or not item:
            return
        if not index:
            index = 0
        for i in range(index):
            if data.default_render_layers_list[i].layer == item.layer:
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


class LIST_OT_AddItemToDefaultRenderLayersList(bpy.types.Operator):
    bl_idname = "default_render_layers_list.add_item"
    bl_label = "Add a layer"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(GoblendContext, context).scene.panel_props.default_render_layers_list) < len(
            layer_items(cls, context)
        )

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(GoblendContext, context)
        # find first unused layer
        existing: set[str] = set()
        for override in ctx.scene.panel_props.default_render_layers_list:
            existing.add(override.layer)
        item = ctx.scene.panel_props.default_render_layers_list.add()
        all_layers = layer_items(self, context)
        for layer in all_layers:
            if layer[0] not in existing:
                item.layer = layer[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromDefaultRenderLayersList(bpy.types.Operator):
    bl_idname = "default_render_layers_list.remove_item"
    bl_label = "Remove a layer"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(GoblendContext, context).scene.panel_props.default_render_layers_list) > 0

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(GoblendContext, context)
        li = ctx.scene.panel_props.default_render_layers_list
        index = ctx.scene.panel_props.default_render_layers_list_index
        li.remove(index)
        ctx.scene.panel_props.default_render_layers_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
