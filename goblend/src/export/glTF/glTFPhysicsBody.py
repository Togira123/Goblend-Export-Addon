# glTFPhysicsBody.py
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


class StringValue(bpy.types.PropertyGroup):
    value: bpy.props.StringProperty()


class IntValue(bpy.types.PropertyGroup):
    value: bpy.props.IntProperty()


class glTFPhysicsBody(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    type: bpy.props.StringProperty()

    layers: bpy.props.CollectionProperty(type=IntValue)
    masks: bpy.props.CollectionProperty(type=IntValue)
    groups: bpy.props.CollectionProperty(type=StringValue)
