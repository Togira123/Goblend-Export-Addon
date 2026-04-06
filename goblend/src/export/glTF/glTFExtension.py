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
from .glTFPhysicsBody import glTFPhysicsBody
from .glTFMaterial import glTFMaterial
from .glTFTextureGroup import glTFTextureGroup
from .glTFGodotScene import glTFGodotScene


class glTFExtension(bpy.types.PropertyGroup):
    save_paths: bpy.props.PointerProperty(type=glTFSavePaths)
    collision_shapes: bpy.props.CollectionProperty(type=glTFCollisionShape)
    physics_bodies: bpy.props.CollectionProperty(type=glTFPhysicsBody)
    materials: bpy.props.CollectionProperty(type=glTFMaterial)
    texture_groups: bpy.props.CollectionProperty(type=glTFTextureGroup)
    # also includes linked collections, not just scenes in GodotScenes
    godot_scenes: bpy.props.CollectionProperty(type=glTFGodotScene)

    is_exporting_with_goblend: bpy.props.BoolProperty(default=False)
