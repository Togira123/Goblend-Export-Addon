# goblend_types.py
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


from typing import TYPE_CHECKING, Any, Callable, NotRequired, TypedDict, Literal

from .blender_types import OperatorReturnItems, ObjectModifierTypeItems

import bpy

# this is needed to not get type errors when accessing these properties
# At runtime it will just be bpy.types.Scene
if TYPE_CHECKING:

    from ..ui.property_groups.AnimationPanelProperties import AnimationPanelProperties
    from ..ui.property_groups.CollisionPanelProperties import CollisionPanelProperties
    from ..ui.property_groups.DefaultCollisionPanelProperties import (
        DefaultCollisionPanelProperties,
    )
    from ..ui.property_groups.GodotScenePanelProperties import GodotScenePanelProperties
    from ..ui.property_groups.LightPanelProperties import LightPanelProperties
    from ..ui.property_groups.MaterialPanelProperties import MaterialPanelProperties
    from ..ui.property_groups.ObjectPanelProperties import ObjectPanelProperties
    from ..ui.property_groups.PanelProperties import PanelProperties

    class GoblendScene(bpy.types.Scene):
        panel_props: PanelProperties

        object_panel_props: bpy.types.bpy_prop_collection_idprop[ObjectPanelProperties]
        material_panel_props: bpy.types.bpy_prop_collection_idprop[MaterialPanelProperties]
        collision_panel_props: bpy.types.bpy_prop_collection_idprop[CollisionPanelProperties]
        animation_panel_props: bpy.types.bpy_prop_collection_idprop[AnimationPanelProperties]
        default_collision_panel_props: DefaultCollisionPanelProperties
        godot_scene_panel_props: bpy.types.bpy_prop_collection_idprop[GodotScenePanelProperties]
        light_panel_props: bpy.types.bpy_prop_collection_idprop[LightPanelProperties]
        show_all_light_settings: bool
        is_root_scene: bool

    class SceneOperators:
        export_to_godot: Callable[None, set[OperatorReturnItems]]

    class GoblendContext(bpy.types.Context):
        scene: GoblendScene

else:
    GoblendScene = bpy.types.Scene
    RegisterGoblendScene = bpy.types.Scene
    SceneOperators = bpy.ops.scene
    GoblendContext = bpy.types.Context


class SettingsForGodotCollision(TypedDict):
    collection: bpy.types.Collection
    type: str
    layer_overrides: None | list[str]
    mask_overrides: None | list[str]
    group_overrides: None | list[str]


class SettingsForGodotObject(TypedDict):
    shadow_cast_mode: str
    name: str
    layer_overrides: NotRequired[list[str]]


class SettingsForGodotAnimation(TypedDict):
    autoplay: bool
    loop: bool


class SettingsForGodotMaterialTransparencyModeOverride(TypedDict):
    mode: str
    scissor: float


class SettingsforGodotLimitUVEffectNormal(TypedDict):
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    obj: bpy.types.Object | None


class SettingsForGodot(TypedDict):
    transparency_mode: str
    scissor_value: float
    cull_mode: str
    default_collision_layers: list[str]
    default_collision_masks: list[str]
    default_groups: list[str]
    default_render_layers: list[str]
    default_physics_type: str
    collisions: list[SettingsForGodotCollision]
    material_transparency_mode_overrides: dict[str, SettingsForGodotMaterialTransparencyModeOverride]
    material_cull_mode_overrides: dict[str, str]
    use_shader_mats: dict[str, bpy.types.Object | None]
    limit_uv_effect_normal: dict[str, SettingsforGodotLimitUVEffectNormal]
    objects: list[SettingsForGodotObject]
    animations: dict[str, SettingsForGodotAnimation]
    godot_scenes: dict[str, str]
    lights: dict[str, dict[str, str | list[str]]]


type UvMapOverrideValueKeys = Literal["Base Color", "Metallic/Roughness", "Normal"]


UvMapOverrideValue = TypedDict(
    "UvMapOverrideValue",
    {
        "Base Color": str,
        "Metallic/Roughness": str,
        "Normal": str,
        "obj": bpy.types.Object,
    },
)

type UvMapOverride = dict[str, UvMapOverrideValue]


class ModifierData(TypedDict):
    name: str
    type: ObjectModifierTypeItems
    props: dict[str, Any]
    node_group: NotRequired[bpy.types.NodeTree]
