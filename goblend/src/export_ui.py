import bpy

from .ui.AddonPreferences import AddonPreferences
from .ui.lists.CollisionLayersList import CollisionLayerListItem, LIST_OT_AddItemToLayersList, LIST_OT_RemoveItemFromLayersList, SCENE_UL_CollisionLayersList
from .ui.lists.CollisionMasksList import CollisionMaskListItem, LIST_OT_AddItemToMasksList, LIST_OT_RemoveItemFromMasksList, SCENE_UL_CollisionMasksList
from .ui.lists.DefaultCollisionLayersList import DefaultCollisionLayerListItem, LIST_OT_AddItemToDefaultLayersList, LIST_OT_RemoveItemFromDefaultLayersList, SCENE_UL_DefaultCollisionLayersList
from .ui.lists.DefaultCollisionMaskList import DefaultCollisionMaskListItem, LIST_OT_AddItemToDefaultMasksList, LIST_OT_RemoveItemFromDefaultMasksList, SCENE_UL_DefaultCollisionMasksList
from .ui.lists.DefaultGroupList import DefaultGroupListItem, LIST_OT_AddItemToDefaultGroupList, LIST_OT_RemoveItemFromDefaultGroupList, SCENE_UL_DefaultGroupList
from .ui.lists.GroupList import GroupListItem, LIST_OT_AddItemToGroupsList, LIST_OT_RemoveItemFromGroupsList, SCENE_UL_GroupsList
from .ui.operators.AddAnimationPanel import SCENE_OT_AddAnimationPanel
from .ui.operators.AddCollisionPanel import SCENE_OT_AddCollisionPanel
from .ui.operators.AddGodotScenesPanel import SCENE_OT_AddGodotScenesPanel
from .ui.operators.AddLightsPanel import SCENE_OT_AddLightsPanel
from .ui.operators.AddObjectConstraints import SCENE_OT_AddObjectConstraints
from .ui.operators.AddObjectConstraintsMaterial import SCENE_OT_AddObjectConstraintsMaterial
from .ui.operators.ExportToGodot import SCENE_OT_ExportToGodot, SCENE_OT_RootExportToGodot
from .ui.operators.RemoveAnimationPanel import SCENE_OT_RemoveAnimationPanel
from .ui.operators.RemoveCollision import SCENE_OT_RemoveCollision
from .ui.operators.RemoveGodotScenesPanel import SCENE_OT_RemoveGodotScenesPanel
from .ui.operators.RemoveLights import SCENE_OT_RemoveLight
from .ui.operators.RemoveObjectConstraints import SCENE_OT_RemoveObjectConstraints
from .ui.operators.RemoveObjectConstraintsMaterial import SCENE_OT_RemoveObjectConstraintsMaterial
from .ui.operators.SyncLights import SCENE_OT_SyncLights
from .ui.operators.SyncMaterialConstraints import SCENE_OT_SyncMaterialConstraints
from .ui.panels.AnimationsPanel import SCENE_PT_AnimationsPanel
from .ui.panels.CollisionsPanel import SCENE_PT_CollisionsPanel
from .ui.panels.ExportPanel import SCENE_PT_ExportPanel
from .ui.panels.GodotScenesPanel import SCENE_PT_GodotScenesPanel
from .ui.panels.LightsPanel import SCENE_PT_LightsPanel
from .ui.panels.ObjectsPanel import SCENE_PT_ObjectsPanel
from .ui.property_groups.AnimationsPanelProperties import AnimationsPanelProperties
from .ui.property_groups.CollisionPanelProperties import CollisionPanelProperties
from .ui.property_groups.DefaultCollisionPanelProperties import DefaultCollisionPanelProperties
from .ui.property_groups.GodotScenesPanelProperties import GodotScenesPanelProperties
from .ui.property_groups.LightPanelProperties import LightPanelProperties
from .ui.property_groups.MaterialOverrideProperties import MaterialOverrideProperties
from .ui.property_groups.ObjectConstraintsPanelProperties import ObjectConstraintsPanelProperties
from .ui.property_groups.PanelProperties import PanelProperties

classes = (
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
    MaterialOverrideProperties, 
    ObjectConstraintsPanelProperties,
    CollisionPanelProperties,
    DefaultCollisionPanelProperties,
    SCENE_OT_RootExportToGodot,
    SCENE_OT_ExportToGodot,
    SCENE_OT_AddObjectConstraints,
    SCENE_OT_AddObjectConstraintsMaterial,
    SCENE_OT_RemoveObjectConstraints,
    SCENE_OT_RemoveObjectConstraintsMaterial,
    SCENE_OT_RemoveCollision,
    SCENE_OT_AddCollisionPanel,
    SCENE_OT_SyncMaterialConstraints,
    SCENE_OT_AddGodotScenesPanel,
    SCENE_OT_SyncLights,
    SCENE_OT_RemoveGodotScenesPanel,
    SCENE_OT_AddLightsPanel,
    SCENE_OT_RemoveLight,
    SCENE_PT_ExportPanel,
    SCENE_PT_ObjectsPanel,
    SCENE_PT_CollisionsPanel,
    SCENE_PT_AnimationsPanel,
    SCENE_PT_GodotScenesPanel,
    SCENE_PT_LightsPanel,
    SCENE_OT_AddAnimationPanel,
    SCENE_OT_RemoveAnimationPanel,
    AnimationsPanelProperties,
    GodotScenesPanelProperties,
    LightPanelProperties
)

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.panel_props = bpy.props.PointerProperty(type=PanelProperties)
    bpy.types.Scene.object_constraints_panel_props = bpy.props.CollectionProperty(type=ObjectConstraintsPanelProperties)
    bpy.types.Scene.collision_panel_props = bpy.props.CollectionProperty(type=CollisionPanelProperties)
    bpy.types.Scene.animations_panel_props = bpy.props.CollectionProperty(type=AnimationsPanelProperties)
    bpy.types.Scene.default_collision_panel_props = bpy.props.PointerProperty(type=DefaultCollisionPanelProperties)
    bpy.types.Scene.godot_scene_panel_props = bpy.props.CollectionProperty(type=GodotScenesPanelProperties)
    bpy.types.Scene.light_panel_props = bpy.props.CollectionProperty(type=LightPanelProperties)
    bpy.types.Scene.show_all_light_settings = bpy.props.BoolProperty(
        name="Show All Light Settings",
        description="Show every available settings instead of only the most important ones. No matter whether this is turned on or off, all properties will be considered when setting these properties in Godot.",
        default=False
    )
    bpy.types.Scene.is_root_scene = bpy.props.BoolProperty(default=True)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.panel_props
    del bpy.types.Scene.object_constraints_panel_props
    del bpy.types.Scene.collision_panel_props
    del bpy.types.Scene.animations_panel_props
    del bpy.types.Scene.default_collision_panel_props
    del bpy.types.Scene.godot_scene_panel_props
    del bpy.types.Scene.light_panel_props
    del bpy.types.Scene.show_all_light_settings
    del bpy.types.Scene.is_root_scene
