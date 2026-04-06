# glTFMaterial.py
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


class glTFMaterialShaderUniform(bpy.types.PropertyGroup):
    var_name: bpy.props.StringProperty()
    uniform_data: bpy.props.StringProperty()


class glTFMaterial(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

    transparency_mode: bpy.props.StringProperty()
    transparency_alpha_scissor_threshold: bpy.props.FloatProperty()
    cull_mode: bpy.props.StringProperty()

    shader_code: bpy.props.StringProperty(default="")
    shader_uniforms: bpy.props.CollectionProperty(type=glTFMaterialShaderUniform)
