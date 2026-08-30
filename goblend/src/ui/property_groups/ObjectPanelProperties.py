# ObjectPanelProperties.py
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


from typing import cast

import bpy

from ...ui.lists.RenderLayersList import RenderLayerListItem
from .enum_items import shadow_cast_enum_items
from ...types.property_types import BoolProp, PointerProp, EnumProp, CollectionProp, IntProp, typed_prop_group


def can_add_object_constraint(self: bpy.types.PropertyGroup, object: bpy.types.Object) -> bool:
    scene = bpy.context.scene
    if object.type != "MESH":
        return False
    if object.library is not None:
        return False

    # this is much slower than a simple bpy.data.collections.get(bpy.context.scene.panel_props.collision_collection),
    # but it only includes collections of the current scene
    # it shouldn't matter too much with a low collection count
    all_collections_in_scene = scene.collection.children_recursive
    collision_collection = None
    for coll in all_collections_in_scene:
        if coll.name == bpy.context.scene.panel_props.collision_collection:
            collision_collection = coll
            break
    if collision_collection and object.name in collision_collection.all_objects:
        return False
    for item in scene.object_panel_props:
        if item.obj == object:
            return False
    return True


@typed_prop_group
class ObjectPanelProperties(bpy.types.PropertyGroup):
    open = BoolProp(default=True)
    obj = PointerProp(
        name="Object",
        type=bpy.types.Object,
        poll=can_add_object_constraint,
    )
    enabled = BoolProp(name="Enable Constraint", description="Whether this constraint should be enabled", default=True)

    def uvmaps(self: "ObjectPanelProperties", context: bpy.types.Context | None) -> list[tuple[str, str, str]]:
        if self.obj:
            return [(uv.name, uv.name, "") for uv in cast(bpy.types.Mesh, self.obj.data).uv_layers][
                :8
            ]  # godot only allows up to 8 uv maps
        return []

    uv_map_enabled = BoolProp(
        name="Override UV Map", description="Whether to use a separate UV Map as bake target", default=False
    )

    uv_map_per_texture_enabled = BoolProp(
        name="Per Texture", description="Whether to use a different UV map per texture", default=False
    )

    uv_map = EnumProp(name="UV Map", items=uvmaps)
    uv_map_base_color = EnumProp(name="Base Color", items=uvmaps)
    uv_map_metallic_roughness = EnumProp(name="Metallic/Roughness", items=uvmaps)
    uv_map_normal = EnumProp(name="Normal", items=uvmaps)

    shadow_cast_mode = EnumProp(
        name="Shadow Cast Mode",
        description="These are the options that 'cast_shadow' has in Godot on a GeometryInstance3D",
        items=shadow_cast_enum_items,
        default="ON",
    )

    render_layers_override_enabled = BoolProp(name="Override Render Layers", default=False)
    render_layers_override_panel_open = BoolProp(default=True)
    render_layers_override_list = CollectionProp(type=RenderLayerListItem)
    render_layers_list_index = IntProp()
