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
