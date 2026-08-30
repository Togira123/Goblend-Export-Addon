# MaterialPanelProperties.py
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

from .enum_items import transparency_enum_items, culling_enum_items
from ...types.property_types import (
    BoolProp,
    PointerProp,
    StringProp,
    IntVectorProp,
    EnumProp,
    IntProp,
    FloatProp,
    typed_prop_group,
)


def can_add_material(self: bpy.types.PropertyGroup, material: bpy.types.Material) -> bool:
    scene = bpy.context.scene
    if material.library is not None:
        return False
    for mat_setting in scene.material_panel_props:
        if mat_setting.mat == material:
            return False
    return True


@typed_prop_group
class MaterialPanelProperties(bpy.types.PropertyGroup):
    open = BoolProp(default=True)
    mat = PointerProp(name="Material", type=bpy.types.Material, poll=can_add_material)

    force_texture_group_disabled = StringProp(
        name="Texture Group",
        description="Texture group cannot be used together with the 'Use Godot Shader' option",
        default="",
    )

    texture_group = StringProp(
        name="Texture Group",
        description="Materials with the same texture group will bake textures to the same image file. Not compatible with 'Use Godot Shader'",
        default="",
    )

    use_shader = BoolProp(
        name="Use Godot Shader",
        description="Attempt to convert this material into a Godot Shader. Only a small subset of nodes is supported, check the documentation to see which.",
        default=False,
    )

    force_override_texture_size_disabled = BoolProp(
        name="Override Texture Size",
        description="You cannot override texture size when using the 'Use Godot Shader' option, as no textures are baked when using it",
        default=False,
    )

    override_texture_size = BoolProp(
        name="Override Texture Size", description="Override texture size for this material", default=False
    )

    texture_dim = IntVectorProp(
        name="Dimensions Override",
        description="Dimensions of the generated texture",
        size=2,
        subtype="COORDINATES",
        default=(1024, 1024),
        min=0,
    )

    force_override_bake_margin_disabled = BoolProp(
        name="Override Bake Margin",
        description="Bake margin cannot be used together with the 'Use Godot Shader' option",
        default=False,
    )

    override_bake_margin = BoolProp(
        name="Override Bake Margin",
        description="Change the bake margin used when baking this material to textures. Not compatible with 'Use Godot Shader'",
        default=False,
    )

    bake_margin = IntProp(
        name="Bake Margin", description="The bake margin to use when baking this material", min=0, default=4
    )

    transparency_mode = EnumProp(
        name="Transparency Mode",
        description="Only affects transparent objects! Transparency mode to use in Godot for this material",
        items=[("DEFAULT", "Default", "Use the default specified at the top global settings")]
        + transparency_enum_items,
        default="DEFAULT",
    )
    transparency_alpha_scissor_threshold = FloatProp(
        name="Scissor Threshold", min=0.0, max=1.0, precision=3, default=0.5
    )

    cull_mode = EnumProp(
        name="Cull Mode",
        description="The cull mode to use for this material in Godot",
        items=[("DEFAULT", "Default", "Use the default specified at the top global settings")] + culling_enum_items,
        default="DEFAULT",
    )

    limit_uv_effect_normal = BoolProp(
        name="Limit Normal UV Effect", description="Define boundaries in which the normal map is applied", default=False
    )
    limit_uv_effect_normal_x_min = FloatProp(name="X Min", min=0.0, max=1.0, precision=6, default=0.0)
    limit_uv_effect_normal_x_max = FloatProp(name="X Max", min=0.0, max=1.0, precision=6, default=1.0)
    limit_uv_effect_normal_y_min = FloatProp(name="Y Min", min=0.0, max=1.0, precision=6, default=0.0)
    limit_uv_effect_normal_y_max = FloatProp(name="Y Max", min=0.0, max=1.0, precision=6, default=1.0)
