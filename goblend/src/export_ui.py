# export_ui.py
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

from .types import GoblendScene, PointerProp, CollectionProp, BoolProp

from .export.glTF.glTFCollisionShape import glTFCollisionShape
from .export.glTF.glTFExtension import glTFExtension
from .export.glTF.glTFGodotScene import glTFGodotScene
from .export.glTF.glTFMaterial import glTFMaterial, glTFMaterialShaderUniform
from .export.glTF.glTFObject import glTFObject
from .export.glTF.glTFPhysicsBody import IntValue, StringValue, glTFPhysicsBody
from .export.glTF.glTFSavePaths import glTFSavePaths
from .export.glTF.glTFTextureGroup import MaterialName, glTFTextureGroup
from .ui.AddonPreferences import AddonPreferences
from .ui.lists.CollisionLayersList import (
    CollisionLayerListItem,
    LIST_OT_AddItemToLayersList,
    LIST_OT_RemoveItemFromLayersList,
    SCENE_UL_CollisionLayersList,
)
from .ui.lists.CollisionMasksList import (
    CollisionMaskListItem,
    LIST_OT_AddItemToMasksList,
    LIST_OT_RemoveItemFromMasksList,
    SCENE_UL_CollisionMasksList,
)
from .ui.lists.DefaultCollisionLayersList import (
    DefaultCollisionLayerListItem,
    LIST_OT_AddItemToDefaultLayersList,
    LIST_OT_RemoveItemFromDefaultLayersList,
    SCENE_UL_DefaultCollisionLayersList,
)
from .ui.lists.DefaultCollisionMaskList import (
    DefaultCollisionMaskListItem,
    LIST_OT_AddItemToDefaultMasksList,
    LIST_OT_RemoveItemFromDefaultMasksList,
    SCENE_UL_DefaultCollisionMasksList,
)
from .ui.lists.DefaultGroupList import (
    DefaultGroupListItem,
    LIST_OT_AddItemToDefaultGroupList,
    LIST_OT_RemoveItemFromDefaultGroupList,
    SCENE_UL_DefaultGroupList,
)
from .ui.lists.DefaultRenderLayersList import (
    DefaultRenderLayerListItem,
    LIST_OT_AddItemToDefaultRenderLayersList,
    LIST_OT_RemoveItemFromDefaultRenderLayersList,
    SCENE_UL_DefaultRenderLayersList,
)
from .ui.lists.GroupList import (
    GroupListItem,
    LIST_OT_AddItemToGroupsList,
    LIST_OT_RemoveItemFromGroupsList,
    SCENE_UL_GroupsList,
)
from .ui.lists.RenderLayersList import (
    LIST_OT_AddItemToRenderLayersList,
    LIST_OT_RemoveItemFromRenderLayersList,
    RenderLayerListItem,
    SCENE_UL_RenderLayersList,
)
from .ui.operators.AddAnimationSetting import SCENE_OT_AddAnimationSetting
from .ui.operators.AddCollisionSetting import SCENE_OT_AddCollisionSetting
from .ui.operators.AddGodotScenesSetting import SCENE_OT_AddGodotScenesSetting
from .ui.operators.AddLightsSetting import SCENE_OT_AddLightsSetting
from .ui.operators.AddMaterialSetting import SCENE_OT_AddMaterialSetting
from .ui.operators.AddObjectSetting import SCENE_OT_AddObjectSetting
from .ui.operators.ExportToGodot import (
    SCENE_OT_ExportToGodot,
    SCENE_OT_RootExportToGodot,
)
from .ui.operators.RemoveAnimationSetting import SCENE_OT_RemoveAnimationSetting
from .ui.operators.RemoveCollisionSetting import SCENE_OT_RemoveCollisionSetting
from .ui.operators.RemoveGodotScenesSetting import SCENE_OT_RemoveGodotScenesSetting
from .ui.operators.RemoveLightSetting import SCENE_OT_RemoveLightSetting
from .ui.operators.RemoveMaterialSetting import SCENE_OT_RemoveMaterialSetting
from .ui.operators.RemoveObjectSetting import SCENE_OT_RemoveObjectSetting
from .ui.operators.SaveSceneInTmpFile import SCENE_OT_SaveSceneInTmpFile
from .ui.operators.SyncLights import SCENE_OT_SyncLights
from .ui.panels.AnimationsPanel import SCENE_PT_AnimationsPanel
from .ui.panels.CollisionsPanel import SCENE_PT_CollisionsPanel
from .ui.panels.ExportPanel import SCENE_PT_ExportPanel
from .ui.panels.GodotScenesPanel import SCENE_PT_GodotScenesPanel
from .ui.panels.LightsPanel import SCENE_PT_LightsPanel
from .ui.panels.MaterialsPanel import SCENE_PT_MaterialsPanel
from .ui.panels.ObjectsPanel import SCENE_PT_ObjectsPanel
from .ui.property_groups.AnimationPanelProperties import AnimationPanelProperties
from .ui.property_groups.CollisionPanelProperties import CollisionPanelProperties
from .ui.property_groups.DefaultCollisionPanelProperties import (
    DefaultCollisionPanelProperties,
)
from .ui.property_groups.GodotScenePanelProperties import GodotScenePanelProperties
from .ui.property_groups.LightPanelProperties import LightPanelProperties
from .ui.property_groups.MaterialPanelProperties import MaterialPanelProperties
from .ui.property_groups.ObjectPanelProperties import ObjectPanelProperties
from .ui.property_groups.PanelProperties import PanelProperties

classes = (
    MaterialName,
    StringValue,
    IntValue,
    glTFMaterialShaderUniform,
    glTFCollisionShape,
    glTFTextureGroup,
    glTFSavePaths,
    glTFPhysicsBody,
    glTFObject,
    glTFMaterial,
    glTFGodotScene,
    glTFExtension,
    CollisionLayerListItem,
    SCENE_UL_CollisionLayersList,
    LIST_OT_AddItemToLayersList,
    LIST_OT_RemoveItemFromLayersList,
    CollisionMaskListItem,
    SCENE_UL_CollisionMasksList,
    LIST_OT_AddItemToMasksList,
    LIST_OT_RemoveItemFromMasksList,
    GroupListItem,
    SCENE_UL_GroupsList,
    LIST_OT_AddItemToGroupsList,
    LIST_OT_RemoveItemFromGroupsList,
    RenderLayerListItem,
    SCENE_UL_RenderLayersList,
    LIST_OT_AddItemToRenderLayersList,
    LIST_OT_RemoveItemFromRenderLayersList,
    DefaultCollisionLayerListItem,
    SCENE_UL_DefaultCollisionLayersList,
    LIST_OT_AddItemToDefaultLayersList,
    LIST_OT_RemoveItemFromDefaultLayersList,
    DefaultCollisionMaskListItem,
    SCENE_UL_DefaultCollisionMasksList,
    LIST_OT_AddItemToDefaultMasksList,
    LIST_OT_RemoveItemFromDefaultMasksList,
    DefaultGroupListItem,
    SCENE_UL_DefaultGroupList,
    LIST_OT_AddItemToDefaultGroupList,
    LIST_OT_RemoveItemFromDefaultGroupList,
    DefaultRenderLayerListItem,
    SCENE_UL_DefaultRenderLayersList,
    LIST_OT_AddItemToDefaultRenderLayersList,
    LIST_OT_RemoveItemFromDefaultRenderLayersList,
    AddonPreferences,
    PanelProperties,
    MaterialPanelProperties,
    ObjectPanelProperties,
    CollisionPanelProperties,
    DefaultCollisionPanelProperties,
    SCENE_OT_RootExportToGodot,
    SCENE_OT_ExportToGodot,
    SCENE_OT_AddObjectSetting,
    SCENE_OT_AddMaterialSetting,
    SCENE_OT_RemoveObjectSetting,
    SCENE_OT_RemoveMaterialSetting,
    SCENE_OT_RemoveCollisionSetting,
    SCENE_OT_AddCollisionSetting,
    SCENE_OT_AddGodotScenesSetting,
    SCENE_OT_SyncLights,
    SCENE_OT_RemoveGodotScenesSetting,
    SCENE_OT_AddLightsSetting,
    SCENE_OT_RemoveLightSetting,
    SCENE_OT_SaveSceneInTmpFile,
    SCENE_PT_ExportPanel,
    SCENE_PT_ObjectsPanel,
    SCENE_PT_MaterialsPanel,
    SCENE_PT_CollisionsPanel,
    SCENE_PT_AnimationsPanel,
    SCENE_PT_GodotScenesPanel,
    SCENE_PT_LightsPanel,
    SCENE_OT_AddAnimationSetting,
    SCENE_OT_RemoveAnimationSetting,
    AnimationPanelProperties,
    GodotScenePanelProperties,
    LightPanelProperties,
)


def register() -> None:
    for c in classes:
        bpy.utils.register_class(c)

    GoblendScene.panel_props = PointerProp(type=PanelProperties)
    GoblendScene.object_panel_props = CollectionProp(type=ObjectPanelProperties)
    GoblendScene.material_panel_props = CollectionProp(type=MaterialPanelProperties)
    GoblendScene.collision_panel_props = CollectionProp(type=CollisionPanelProperties)
    GoblendScene.animation_panel_props = CollectionProp(type=AnimationPanelProperties)
    GoblendScene.default_collision_panel_props = PointerProp(type=DefaultCollisionPanelProperties)
    GoblendScene.godot_scene_panel_props = CollectionProp(type=GodotScenePanelProperties)
    GoblendScene.light_panel_props = CollectionProp(type=LightPanelProperties)
    GoblendScene.show_all_light_settings = BoolProp(
        name="Show All Light Settings",
        description="Show every available settings instead of only the most important ones. No matter whether this is turned on or off, all properties will be considered when setting these properties in Godot.",
        default=False,
    )
    GoblendScene.is_root_scene = BoolProp(default=True)


def unregister() -> None:
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del GoblendScene.panel_props
    del GoblendScene.object_panel_props
    del GoblendScene.material_panel_props
    del GoblendScene.collision_panel_props
    del GoblendScene.animation_panel_props
    del GoblendScene.default_collision_panel_props
    del GoblendScene.godot_scene_panel_props
    del GoblendScene.light_panel_props
    del GoblendScene.show_all_light_settings
    del GoblendScene.is_root_scene
