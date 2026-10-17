# glTFSavePaths.py
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

from ...types.property_types import typed_prop_group, StringProp


@typed_prop_group
class glTFSavePaths(bpy.types.PropertyGroup):
    scene_save_path = StringProp()
    material_save_path = StringProp()
    texture_save_path = StringProp()
    animation_library_save_path = StringProp()
    animation_save_path = StringProp()
    shader_save_path = StringProp()
    collision_shapes_save_path = StringProp()
    mesh_save_path = StringProp()
    curve_save_path = StringProp()

    @classmethod
    def paths(cls) -> list[str]:
        return list(cls.__annotations__.keys())
