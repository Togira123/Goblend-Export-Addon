# glTF2ExportUserExtension.py
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
from mathutils import Quaternion

from ..export.glTF.glTFObject import glTFObject

from ..export.glTF.glTFGodotScene import glTFGodotScene
from ..ui.property_groups.LightPanelProperties import LightPanelProperties

from ..types.goblend_types import GoblendContext, GoblendScene
from ..log import log
from typing import TYPE_CHECKING, Required, TypedDict, cast, Literal, Any

if TYPE_CHECKING:
    from io_scene_gltf2.io.com.gltf2_io import Gltf, Scene, Material, Node, Animation, RealizedNode, Mesh
    from io_scene_gltf2.io.com.gltf2_io_extensions import Extension, ChildOfRootExtension

omi_physics_body = "OMI_physics_body"
omi_physics_shape = "OMI_physics_shape"
goblend_physics_body_attribute = "EXT_goblend_physics_body_attribute"
goblend_material = "EXT_goblend_material"
goblend_light = "EXT_goblend_light"
goblend_general = "EXT_goblend_general"
goblend_godot_scene = "EXT_goblend_godot_scene"
goblend_animation = "EXT_goblend_animation"
goblend_object = "EXT_goblend_object"
godot_single_root = "GODOT_single_root"


class GoblendMaterialExtShaderUniform(TypedDict):
    var_name: str
    uniform_data: str


class GoblendMaterialExt(TypedDict, total=False):
    transparency_mode: Required[str]
    transparency_alpha_scissor_threshold: float
    shader_code: str
    shader_uniforms: list[GoblendMaterialExtShaderUniform]
    cull_mode: Required[str]


class GoblendObjectExt(TypedDict, total=False):
    render_layers: Required[list[int]]
    shadow_cast_mode: str


class GoblendLightExt(TypedDict):
    omni_range: float
    omni_attenuation: float
    omni_shadow_mode: int
    spot_range: float
    spot_attenuation: float
    spot_angle: float
    spot_angle_attenuation: float
    light_color: list[float]
    light_energy: float
    light_indirect_energy: float
    light_volumetric_fog_energy: float
    light_angular_distance: float
    light_size: float
    light_negative: bool
    light_specular: float
    light_bake_mode: int
    light_cull_mask: int
    shadow_enabled: bool


class GoblendGeneralExt(TypedDict):
    save_paths: dict[str, str]


# need to add some arbitrary extension for GODOT_single_root to be in extensions_used
class GoblendSingleRootExt(TypedDict):
    foo: list[bool]


class GoblendGodotSceneExt(TypedDict):
    scene_path: str


class GoblendAnimationExt(TypedDict):
    autoplay: bool
    loop: bool


class GoblendPhysicsBodyAttributesExt(TypedDict, total=False):
    layers: list[int] | None
    masks: list[int] | None
    groups: list[str] | None


class OMIPhysicsBodyExtTrigger(TypedDict, total=False):
    nodes: list[int]
    shape: "ChildOfRootExtension | None"


class OMIPhysicsBodyExtMotion(TypedDict):
    type: Literal["static", "kinematic", "dynamic", "character"]


class OMIPhysicsBodyExtCollider(TypedDict):
    shape: "ChildOfRootExtension | None"


class OMIPhysicsBodyExt(TypedDict, total=False):
    trigger: OMIPhysicsBodyExtTrigger
    motion: OMIPhysicsBodyExtMotion
    collider: OMIPhysicsBodyExtCollider


# this class is special, it is used to add a gltf extension
# it must be defined in the __init__.py file for it to work
# hence we import it there
class glTF2ExportUserExtension:
    if TYPE_CHECKING:
        from io_scene_gltf2.io.com.gltf2_io_extensions import (
            Extension as glTFExtension,
            ChildOfRootExtension as glTFChildOfRootExtension,
        )

        from io_scene_gltf2.io.com.gltf2_io import Node

        Extension: type[glTFExtension]
        ChildOfRootExtension: type[glTFChildOfRootExtension]
        godot_scenes_dict: dict[str, glTFGodotScene]
        root_node: Node | None
        blender_object_name_to_gltf_node: dict[str, Node]
        object_props_dict: dict[str, glTFObject]

    def __init__(self) -> None:
        _init(self)

    def gather_gltf_extensions_hook(self, gltf2_plan: "Gltf", _export_settings: dict[Any, Any]) -> None:
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_gltf_extensions_hook(self, gltf2_plan)

    def gather_scene_hook(
        self, gltf2_scene: "Scene", blender_scene: GoblendScene, _export_settings: dict[Any, Any]
    ) -> None:
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_scene_hook(self, gltf2_scene, blender_scene)

    def gather_node_hook(
        self, gltf2_object: "Node", blender_object: bpy.types.Object, _export_settings: dict[Any, Any]
    ) -> None:
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_node_hook(self, gltf2_object, blender_object)

    def gather_gltf_hook(
        self,
        _active_scene_idx: int,
        _scenes: list["Scene"],
        animations: list["Animation"],
        _export_settings: dict[Any, Any],
    ) -> None:
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_gltf_hook(self, animations)


def _init(self: glTF2ExportUserExtension) -> None:
    from io_scene_gltf2.io.com.gltf2_io_extensions import Extension, ChildOfRootExtension

    self.Extension = Extension
    self.ChildOfRootExtension = ChildOfRootExtension
    self.godot_scenes_dict = {}
    self.root_node = None
    self.blender_object_name_to_gltf_node = {}
    scene = cast(GoblendScene, bpy.context.scene)
    for godot_scene in scene.panel_props.gltf_extension.godot_scenes:
        self.godot_scenes_dict[godot_scene.object_name] = godot_scene
    self.object_props_dict = {}
    for object_prop in scene.panel_props.gltf_extension.objects:
        self.object_props_dict[object_prop.name] = object_prop


def _gather_gltf_extensions_hook(self: glTF2ExportUserExtension, gltf2_plan: "Gltf") -> None:
    if gltf2_plan.extensions is None:
        gltf2_plan.extensions = {}

    ctx = cast(GoblendContext, bpy.context)

    gltf_extension = ctx.scene.panel_props.gltf_extension
    # add save paths
    paths: dict[str, str] = {}
    path_keys = gltf_extension.save_paths.paths()
    for path_key in path_keys:
        paths[path_key] = getattr(gltf_extension.save_paths, path_key)

    general_ext: GoblendGeneralExt = {"save_paths": paths}

    gltf2_plan.extensions[goblend_general] = self.Extension(name=goblend_general, extension=general_ext, required=False)
    # need to add some arbitrary property for GODOT_single_root to be in extensions_used
    # since we set it to an empty array it won't be added in the "extensions" dict
    # but still be under "extensionsUsed"
    dummy_ext: GoblendSingleRootExt = {"foo": []}
    gltf2_plan.extensions[godot_single_root] = self.Extension(
        name=godot_single_root, extension=dummy_ext, required=False
    )

    # have to ensure that root node is at position 0
    if len(gltf2_plan.nodes) > 1 and gltf2_plan.nodes[0] != self.root_node:
        # make sure to place the root node at first place
        index_of_root_node = gltf2_plan.nodes.index(cast("RealizedNode", self.root_node))
        gltf2_plan.nodes[0], gltf2_plan.nodes[index_of_root_node] = (
            gltf2_plan.nodes[index_of_root_node],
            gltf2_plan.nodes[0],
        )
        # now we also need to change indices where applicable
        if len(gltf2_plan.scenes) > 0:
            gltf2_plan.scenes[0].nodes = [0]
        for node in gltf2_plan.nodes:
            # swap indices of children
            for i in range(len(node.children)):
                if node.children[i] == 0:
                    node.children[i] = index_of_root_node
                elif node.children[i] == index_of_root_node:
                    node.children[i] = 0
        for animation in gltf2_plan.animations:
            if not animation.channels:
                continue
            for channel in animation.channels:
                if not channel.target:
                    continue
                channel_extensions = channel.target.extensions
                if not channel_extensions:
                    continue
                for ext_name in channel_extensions:
                    ext = channel_extensions[ext_name]
                    if ext_name != "KHR_animation_pointer" or "pointer" not in ext:
                        continue
                    if ext["pointer"].startswith("/nodes/"):
                        node_idx = ext["pointer"][len("/nodes/") : ext["pointer"].index("/", len("/nodes/"))]
                        if node_idx == "0":
                            ext["pointer"] = "/nodes/" + str(index_of_root_node) + ext["pointer"][len("/nodes/0") :]
                        elif node_idx == str(index_of_root_node):
                            ext["pointer"] = "/nodes/0" + ext["pointer"][len("/nodes/" + str(index_of_root_node)) :]


def _gather_scene_hook(self: glTF2ExportUserExtension, gltf2_scene: "Scene", blender_scene: GoblendScene) -> None:
    gltf_extension = blender_scene.panel_props.gltf_extension
    collisions_collection = bpy.context.scene.panel_props.collision_collection

    texture_group_dict: dict[str, str] = {}
    for texture_group in gltf_extension.texture_groups:
        for mat_name in texture_group.materials:
            texture_group_dict[mat_name.name] = texture_group.name

    materials: set["Material"] = set()
    for node in gltf2_scene.nodes:
        if node.mesh:
            for primitive in node.mesh.primitives:
                if primitive.material:
                    materials.add(primitive.material)

    # iterate over all materials, if it belongs to a texture group rename it the first time and otherwise discard it
    material_dict: dict[str, "Material"] = {}
    for material in materials:
        if material.name in texture_group_dict:
            actual_name = texture_group_dict[material.name]
            if actual_name in material_dict:
                continue  # already added this texture group
            material.name = actual_name

        material_dict[material.name] = material
    # replace materials with their texture group material if applicable
    for node in gltf2_scene.nodes:
        if node.mesh:
            for primitive in node.mesh.primitives:
                if primitive.material and primitive.material.name in texture_group_dict:
                    primitive.material = material_dict[texture_group_dict[primitive.material.name]]

    # apply extension settings to materials
    for material in gltf_extension.materials:
        mat_name = material.name
        if mat_name in texture_group_dict:
            mat_name = texture_group_dict[mat_name]
        if mat_name not in material_dict:
            continue
        material_node = material_dict[mat_name]
        ext: GoblendMaterialExt = {"transparency_mode": material.transparency_mode, "cull_mode": material.cull_mode}
        if material.transparency_mode == "SCISSOR":
            ext["transparency_alpha_scissor_threshold"] = material.transparency_alpha_scissor_threshold
        if material.shader_code != "":
            ext["shader_code"] = material.shader_code
            ext["shader_uniforms"] = []
            for uniform in material.shader_uniforms:
                ext["shader_uniforms"].append({"var_name": uniform.var_name, "uniform_data": uniform.uniform_data})
        material_node.extensions[goblend_material] = self.Extension(
            name=goblend_material,
            extension=ext,
            required=False,
        )

    # get physics types to distinguish between area shapes and body shapes
    physics_body_types: dict[str, str] = {}
    for physics_body in gltf_extension.physics_bodies:
        physics_body_types[physics_body.name] = physics_body.type

    # create shape nodes
    shapes_dict: dict[str, list["Node"]] = {}
    for shape in gltf_extension.collision_shapes:
        gltf2_scene.nodes.remove(self.blender_object_name_to_gltf_node[shape.object.name])
        parent_type = None
        if shape.parent_name in physics_body_types:
            parent_type = physics_body_types[shape.parent_name]
        else:
            # the parent isn't its own physics body hence it is the type of the root
            parent_type = physics_body_types[collisions_collection]
        shape_node = None
        if shape.type == "box":
            shape_node = _add_box_shape(
                self,
                shape.object,
                parent_type == "AREA",
                shape.dimensions[0],
                shape.dimensions[1],
                shape.dimensions[2],
            )
        elif shape.type == "cylinder":
            shape_node = _add_cylinder_shape(
                self,
                shape.object,
                parent_type == "AREA",
                shape.radius,
                shape.height,
            )
        elif shape.type == "sphere":
            shape_node = _add_sphere_shape(self, shape.object, parent_type == "AREA", shape.radius)
        elif shape.type == "convcol":
            shape_node = _add_convex_shape(
                self,
                shape.object,
                parent_type == "AREA",
                self.blender_object_name_to_gltf_node[shape.object.name].mesh,
            )
        else:
            # unknown shape type
            log("Unknown shape type: " + shape.type, "WARNING")
            continue
        if next((b for b in gltf_extension.physics_bodies if b.name == shape.parent_name), None):
            if shape.parent_name not in shapes_dict:
                shapes_dict[shape.parent_name] = []
            shapes_dict[shape.parent_name].append(shape_node)
        else:
            # if the parent collection isn't a physics body (because it wasn't added as a setting) add the shape to the "Collisions" collection
            if collisions_collection not in shapes_dict:
                shapes_dict[collisions_collection] = []
            shapes_dict[collisions_collection].append(shape_node)
    root_physics_body_node = None
    for physics_body in gltf_extension.physics_bodies:
        if physics_body.name not in shapes_dict:
            # body has no shapes
            shapes_dict[physics_body.name] = []
        # place the collision shape centered in terms of origins of the shapes
        # unless it is the root node
        translation = (
            _get_middle_point(shapes_dict[physics_body.name])
            if physics_body.name != collisions_collection
            else [0.0, 0.0, 0.0]
        )
        physics_body_node = _create_physics_body(
            self,
            physics_body.type,
            None,
            physics_body.name,
            translation=translation,
            layers=[layer.value for layer in physics_body.layers] if physics_body.type != "NODE" else None,
            masks=[mask.value for mask in physics_body.masks] if physics_body.type != "NODE" else None,
            groups=[group.value for group in physics_body.groups] if physics_body.type != "NODE" else None,
        )

        # change child translation to still have same absolute position
        for shape_node in shapes_dict[physics_body.name]:
            shape_node.translation[0] -= translation[0]
            shape_node.translation[1] -= translation[1]
            shape_node.translation[2] -= translation[2]

        physics_body_node.children = shapes_dict[physics_body.name]
        if (
            omi_physics_body in physics_body_node.extensions
            and "trigger" in physics_body_node.extensions[omi_physics_body].extension
        ):  # area node, set its trigger to all its collision shapes
            physics_body_node.extensions[omi_physics_body].extension["trigger"] = shapes_dict[physics_body.name]
        if physics_body_node.name == collisions_collection:
            # rename the root node to the scene name
            physics_body_node.name = gltf_extension.scene_name
            root_physics_body_node = physics_body_node
        # add node to the scene
        gltf2_scene.nodes.append(physics_body_node)
    children_of_root: list["Node"] = []
    for node in gltf2_scene.nodes:
        if node != root_physics_body_node:
            children_of_root.append(node)
    # make the root node the only scene child and add the rest as children of that root node
    # it is guaranteed that root_physics_body_node is not None here
    gltf2_scene.nodes = [cast("Node", root_physics_body_node)]
    cast("Node", root_physics_body_node).children.extend(children_of_root)
    self.root_node = root_physics_body_node


def _gather_node_hook(self: glTF2ExportUserExtension, gltf2_object: "Node", blender_object: bpy.types.Object) -> None:
    scene = cast(GoblendScene, bpy.context.scene)
    self.blender_object_name_to_gltf_node[blender_object.name] = gltf2_object
    if blender_object.name in self.godot_scenes_dict:
        # is godot scene
        if gltf2_object.extensions is None:
            gltf2_object.extensions = {}
        scene_ext: GoblendGodotSceneExt = {
            "scene_path": self.godot_scenes_dict[blender_object.name].scene_path,
        }
        gltf2_object.extensions[goblend_godot_scene] = self.Extension(
            name=goblend_godot_scene,
            extension=scene_ext,
            required=False,
        )
        gltf2_object.mesh = None
        return

    is_light = gltf2_object.extensions and "KHR_lights_punctual" in gltf2_object.extensions

    if gltf2_object.extensions is None:
        gltf2_object.extensions = {}

    if blender_object.name in self.object_props_dict:
        props = self.object_props_dict[blender_object.name]
        ext_obj: GoblendObjectExt = {
            "render_layers": [layer.value for layer in props.render_layers],
        }
        if not is_light:
            ext_obj["shadow_cast_mode"] = props.shadow_cast_mode
        gltf2_object.extensions[goblend_object] = self.Extension(name=goblend_object, extension=ext_obj, required=False)
    else:
        ext_obj = {"render_layers": [layer.value for layer in scene.panel_props.gltf_extension.default_render_layers]}
        gltf2_object.extensions[goblend_object] = self.Extension(name=goblend_object, extension=ext_obj, required=False)

    if is_light:
        light_settings: LightPanelProperties | None = None
        for setting in scene.light_panel_props:
            if setting.light == blender_object:
                light_settings = setting
                break
        if not light_settings:
            return
        ext: GoblendLightExt = {
            "omni_range": light_settings.omni_range,
            "omni_attenuation": light_settings.omni_attenuation,
            "omni_shadow_mode": int(light_settings.omni_shadow_mode),
            "spot_range": light_settings.spot_range,
            "spot_attenuation": light_settings.spot_attenuation,
            "spot_angle": light_settings.spot_angle,
            "spot_angle_attenuation": light_settings.spot_angle_attenuation,
            "light_color": [x for x in light_settings.light_color],
            "light_energy": light_settings.light_energy,
            "light_indirect_energy": light_settings.light_indirect_energy,
            "light_volumetric_fog_energy": light_settings.light_volumetric_fog_energy,
            "light_angular_distance": light_settings.light_angular_distance,
            "light_size": light_settings.light_size,
            "light_negative": light_settings.light_negative,
            "light_specular": light_settings.light_specular,
            "light_bake_mode": int(light_settings.light_bake_mode),
            "light_cull_mask": light_settings.light_cull_mask,
            "shadow_enabled": light_settings.shadow_enabled,
        }
        gltf2_object.extensions[goblend_light] = self.Extension(name=goblend_light, extension=ext, required=False)
        return


def _gather_gltf_hook(self: glTF2ExportUserExtension, animations: list["Animation"]) -> None:
    # NOTE: animating alpha value is broken before blender 5.1
    # the experimental option of Blender's gltf exporter "export_convert_animation_pointer" will take care of material animations
    animation_props = bpy.context.scene.animation_panel_props
    for animation in animations:
        # find if there's an animation prop for it
        anim_prop = None
        for animation_prop in animation_props:
            if animation_prop.animation.name == animation.name:
                anim_prop = animation_prop
                break
        if anim_prop is None:
            continue
        ext: GoblendAnimationExt = {"autoplay": anim_prop.autoplay, "loop": anim_prop.loop}
        if animation.extensions is None:
            animation.extensions = {}
        animation.extensions[goblend_animation] = self.Extension(name=goblend_animation, extension=ext, required=False)


def _get_middle_point(shapes: list["Node"]) -> list[float]:
    if len(shapes) == 0:
        return [0.0, 0.0, 0.0]
    xmin = shapes[0].translation[0]
    xmax = shapes[0].translation[0]
    ymin = shapes[0].translation[1]
    ymax = shapes[0].translation[1]
    zmin = shapes[0].translation[2]
    zmax = shapes[0].translation[2]
    for shape_node in shapes:
        if shape_node.translation[0] < xmin:
            xmin = shape_node.translation[0]
        elif shape_node.translation[0] > xmax:
            xmax = shape_node.translation[0]
        if shape_node.translation[1] < ymin:
            ymin = shape_node.translation[1]
        elif shape_node.translation[1] > ymax:
            ymax = shape_node.translation[1]
        if shape_node.translation[2] < zmin:
            zmin = shape_node.translation[2]
        elif shape_node.translation[2] > zmax:
            zmax = shape_node.translation[2]
    return [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]


def _create_node(
    name: str,
    extensions: dict[str, "Extension"] = {},
    translation: list[float] = [0, 0, 0],
    rotation: list[float] | None = None,
) -> "Node":
    from io_scene_gltf2.io.com import gltf2_io
    from io_scene_gltf2.blender.com import gltf2_blender_math

    # convert rotation to use y up
    if rotation:
        rot = [rotation[0], rotation[1], rotation[3], -rotation[2]]
        rot[0], rot[1], rot[2], rot[3] = (
            gltf2_blender_math.round_if_near(rot[0], 1.0),
            gltf2_blender_math.round_if_near(rot[1], 0.0),
            gltf2_blender_math.round_if_near(rot[2], 0.0),
            gltf2_blender_math.round_if_near(rot[3], 0.0),
        )
        if rot[0] != 1.0 or rot[1] != 0.0 or rot[2] != 0.0 or rot[3] != 0.0:
            rotation = [rot[1], rot[2], rot[3], rot[0]]
        else:
            rotation = None

    return gltf2_io.Node(
        name=name,
        extensions=extensions,
        translation=translation,
        rotation=rotation,
        matrix=[],
        camera=None,
        children=[],
        extras=None,
        mesh=None,
        scale=None,
        skin=None,
        weights=None,
    )


def _create_physics_body(
    self: glTF2ExportUserExtension,
    type: str | None,
    shape: "ChildOfRootExtension | None",
    name: str,
    is_area_shape: bool = False,
    translation: list[float] = [0, 0, 0],
    rotation: list[float] | None = None,
    layers: list[int] | None = None,
    masks: list[int] | None = None,
    groups: list[str] | None = None,
) -> "Node":
    ext: dict[str, "Extension"] = {}
    physics_body_ext: OMIPhysicsBodyExt = {}
    if type and type != "NODE":
        if type == "AREA":
            # continue here, set up trigger correctly
            physics_body_ext["trigger"] = {"nodes": []}
        else:
            omi_type = "static"
            if type == "ANIMATABLE_BODY":
                omi_type = "kinematic"
            elif type == "RIGID_BODY":
                omi_type = "dynamic"
            elif type == "CHARACTER":
                # seems to be supported in Godot source code but marked as deprecated so watch out for that
                # https://github.com/godotengine/godot/blob/db5da10d21bad1691865b188c55a208d26ad3b33/modules/gltf/extensions/physics/gltf_physics_body.cpp#L280
                omi_type = "character"

            physics_body_ext["motion"] = {"type": omi_type}
    if shape is not None:
        if is_area_shape:
            physics_body_ext["trigger"] = {"shape": shape}
        else:
            physics_body_ext["collider"] = {"shape": shape}
    if physics_body_ext:
        ext[omi_physics_body] = self.Extension(name=omi_physics_body, extension=physics_body_ext, required=False)

    physics_body_attributes_ext: GoblendPhysicsBodyAttributesExt = {}
    if layers is not None:
        physics_body_attributes_ext["layers"] = layers
    if masks is not None:
        physics_body_attributes_ext["masks"] = masks
    if groups is not None:
        physics_body_attributes_ext["groups"] = groups

    if physics_body_attributes_ext:
        ext[goblend_physics_body_attribute] = self.Extension(
            name=goblend_physics_body_attribute, extension=physics_body_attributes_ext, required=False
        )

    return _create_node(
        name,
        extensions=ext,
        translation=translation,
        rotation=rotation,
    )


def _add_box_shape(
    self: glTF2ExportUserExtension, obj: bpy.types.Object, is_area_shape: bool, dim_x: float, dim_y: float, dim_z: float
) -> "Node":
    shape = self.ChildOfRootExtension(
        path=["shapes"],
        name=omi_physics_shape,
        extension={
            "type": "box",
            "box": {
                # swap y and z as godot uses y for up/down
                "size": [dim_x, dim_z, dim_y]
            },
        },
        required=False,
    )
    return _create_shape_node(self, obj, shape, is_area_shape)


def _add_cylinder_shape(
    self: glTF2ExportUserExtension, obj: bpy.types.Object, is_area_shape: bool, radius: float, height: float
) -> "Node":
    shape = self.ChildOfRootExtension(
        path=["shapes"],
        name=omi_physics_shape,
        extension={
            "type": "cylinder",
            # we do not use radiusTop and radiusBottom here since the godot implementation
            # only checks the radius property, even though this does not seem to be correct by the spec
            # https://github.com/omigroup/gltf-extensions/blob/main/extensions/2.0/OMI_physics_shape/README.md
            "cylinder": {"height": height, "radius": radius},
        },
        required=False,
    )
    return _create_shape_node(self, obj, shape, is_area_shape)


def _add_sphere_shape(
    self: glTF2ExportUserExtension, obj: bpy.types.Object, is_area_shape: bool, radius: float
) -> "Node":
    shape = self.ChildOfRootExtension(
        path=["shapes"],
        name=omi_physics_shape,
        extension={
            "type": "sphere",
            "sphere": {"radius": radius},
        },
        required=False,
    )
    return _create_shape_node(self, obj, shape, is_area_shape)


def _add_convex_shape(
    self: glTF2ExportUserExtension, obj: bpy.types.Object, is_area_shape: bool, mesh: "Mesh | None"
) -> "Node":
    shape = self.ChildOfRootExtension(
        path=["shapes"], name=omi_physics_shape, extension={"type": "convex", "convex": {"mesh": mesh}}, required=False
    )
    return _create_shape_node(self, obj, shape, is_area_shape)


def _create_shape_node(
    self: glTF2ExportUserExtension, obj: bpy.types.Object, shape: "ChildOfRootExtension", is_area_shape: bool
) -> "Node":
    # swap y and z as godot uses y for up/down
    translation = [obj.location[0], obj.location[2], -obj.location[1]]
    rotation = None
    if obj.rotation_mode == "QUATERNION":
        rotation = [a for a in obj.rotation_quaternion]
    elif obj.rotation_mode == "AXIS_ANGLE":
        rotation = [
            a
            for a in Quaternion(
                cast(list[float], obj.rotation_axis_angle)[1:], cast(list[float], obj.rotation_axis_angle)[0]
            )
        ]
    else:
        rotation = [a for a in obj.rotation_euler.to_quaternion()]
    return _create_physics_body(
        self, None, shape, obj.name, is_area_shape=is_area_shape, translation=translation, rotation=rotation
    )
