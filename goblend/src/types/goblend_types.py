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


from typing import TYPE_CHECKING, Callable, Literal

import bpy

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

OperatorReturnItems = Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]

# this is needed to not get type errors when accessing these properties
# At runtime it will just be bpy.types.Scene
if TYPE_CHECKING:

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
