import bpy

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
from .ui.lists.GroupList import (
    GroupListItem,
    LIST_OT_AddItemToGroupsList,
    LIST_OT_RemoveItemFromGroupsList,
    SCENE_UL_GroupsList,
)
from .ui.operators.AddAnimationSetting import SCENE_OT_AddAnimationSetting
from .ui.operators.AddCollisionSetting import SCENE_OT_AddCollisionSetting
from .ui.operators.AddGodotScenesSetting import SCENE_OT_AddGodotScenesSetting
from .ui.operators.AddLightsSetting import SCENE_OT_AddLightsSetting
from .ui.operators.AddObjectSetting import SCENE_OT_AddObjectSetting
from .ui.operators.AddMaterialSetting import SCENE_OT_AddMaterialSetting
from .ui.operators.ExportToGodot import SCENE_OT_ExportToGodot, SCENE_OT_RootExportToGodot
from .ui.operators.RemoveAnimationSetting import SCENE_OT_RemoveAnimationSetting
from .ui.operators.RemoveCollisionSetting import SCENE_OT_RemoveCollisionSetting
from .ui.operators.RemoveGodotScenesSetting import SCENE_OT_RemoveGodotScenesSetting
from .ui.operators.RemoveLightSetting import SCENE_OT_RemoveLightSetting
from .ui.operators.RemoveObjectSetting import SCENE_OT_RemoveObjectSetting
from .ui.operators.RemoveMaterialSetting import SCENE_OT_RemoveMaterialSetting
from .ui.operators.SyncLights import SCENE_OT_SyncLights
from .ui.panels.AnimationsPanel import SCENE_PT_AnimationsPanel
from .ui.panels.CollisionsPanel import SCENE_PT_CollisionsPanel
from .ui.panels.ExportPanel import SCENE_PT_ExportPanel
from .ui.panels.GodotScenesPanel import SCENE_PT_GodotScenesPanel
from .ui.panels.LightsPanel import SCENE_PT_LightsPanel
from .ui.panels.ObjectsPanel import SCENE_PT_ObjectsPanel
from .ui.panels.MaterialsPanel import SCENE_PT_MaterialsPanel
from .ui.property_groups.AnimationPanelProperties import AnimationPanelProperties
from .ui.property_groups.CollisionPanelProperties import CollisionPanelProperties
from .ui.property_groups.DefaultCollisionPanelProperties import DefaultCollisionPanelProperties
from .ui.property_groups.GodotScenePanelProperties import GodotScenePanelProperties
from .ui.property_groups.LightPanelProperties import LightPanelProperties
from .ui.property_groups.MaterialPanelProperties import MaterialPanelProperties
from .ui.property_groups.ObjectPanelProperties import ObjectPanelProperties
from .ui.property_groups.PanelProperties import PanelProperties

from .export.glTF.glTFCollisionShape import glTFCollisionShape
from .export.glTF.glTFSavePaths import glTFSavePaths
from .export.glTF.glTFTextureGroup import glTFTextureGroup, MaterialName
from .export.glTF.glTFPhysicsBody import glTFPhysicsBody, StringValue, IntValue
from .export.glTF.glTFMaterial import glTFMaterial, glTFMaterialShaderUniform
from .export.glTF.glTFGodotScene import glTFGodotScene
from .export.glTF.glTFExtension import glTFExtension

classes = (
    MaterialName,
    StringValue,
    IntValue,
    glTFMaterialShaderUniform,
    glTFCollisionShape,
    glTFTextureGroup,
    glTFSavePaths,
    glTFPhysicsBody,
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


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.panel_props = bpy.props.PointerProperty(type=PanelProperties)
    bpy.types.Scene.object_panel_props = bpy.props.CollectionProperty(type=ObjectPanelProperties)
    bpy.types.Scene.material_panel_props = bpy.props.CollectionProperty(type=MaterialPanelProperties)
    bpy.types.Scene.collision_panel_props = bpy.props.CollectionProperty(type=CollisionPanelProperties)
    bpy.types.Scene.animation_panel_props = bpy.props.CollectionProperty(type=AnimationPanelProperties)
    bpy.types.Scene.default_collision_panel_props = bpy.props.PointerProperty(type=DefaultCollisionPanelProperties)
    bpy.types.Scene.godot_scene_panel_props = bpy.props.CollectionProperty(type=GodotScenePanelProperties)
    bpy.types.Scene.light_panel_props = bpy.props.CollectionProperty(type=LightPanelProperties)
    bpy.types.Scene.show_all_light_settings = bpy.props.BoolProperty(
        name="Show All Light Settings",
        description="Show every available settings instead of only the most important ones. No matter whether this is turned on or off, all properties will be considered when setting these properties in Godot.",
        default=False,
    )
    bpy.types.Scene.is_root_scene = bpy.props.BoolProperty(default=True)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.panel_props
    del bpy.types.Scene.object_panel_props
    del bpy.types.Scene.material_panel_props
    del bpy.types.Scene.collision_panel_props
    del bpy.types.Scene.animation_panel_props
    del bpy.types.Scene.default_collision_panel_props
    del bpy.types.Scene.godot_scene_panel_props
    del bpy.types.Scene.light_panel_props
    del bpy.types.Scene.show_all_light_settings
    del bpy.types.Scene.is_root_scene
