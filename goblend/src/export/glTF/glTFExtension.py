# glTFExtension.py
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
from .glTFSavePaths import glTFSavePaths
from .glTFCollisionShape import glTFCollisionShape
from .glTFPhysicsBody import glTFPhysicsBody, IntValue
from .glTFObject import glTFObject
from .glTFMaterial import glTFMaterial
from .glTFTextureGroup import glTFTextureGroup
from .glTFGodotScene import glTFGodotScene

from ...types.property_types import typed_prop_group, PointerProp, CollectionProp, StringProp, BoolProp


@typed_prop_group
class glTFExtension(bpy.types.PropertyGroup):
    save_paths = PointerProp(type=glTFSavePaths)
    collision_shapes = CollectionProp(type=glTFCollisionShape)
    physics_bodies = CollectionProp(type=glTFPhysicsBody)
    objects = CollectionProp(type=glTFObject)
    materials = CollectionProp(type=glTFMaterial)
    texture_groups = CollectionProp(type=glTFTextureGroup)
    # also includes linked collections, not just scenes in GodotScenes
    godot_scenes = CollectionProp(type=glTFGodotScene)

    default_render_layers = CollectionProp(type=IntValue)

    # scene name
    scene_name = StringProp()

    is_exporting_with_goblend = BoolProp(default=False)
