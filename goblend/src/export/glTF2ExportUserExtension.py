import os
import bpy
from mathutils import Quaternion
from ..log import log

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

collisions_collection = "Collisions"


# this class is special, it is used to add a gltf extension
# it must be defined in the __init__.py file for it to work
# hence we import it there
class glTF2ExportUserExtension:
    def __init__(self):
        _init(self)

    def gather_gltf_extensions_hook(self, gltf2_plan, _export_settings):
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_gltf_extensions_hook(self, gltf2_plan)

    def gather_scene_hook(self, gltf2_scene, blender_scene, _export_settings):
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_scene_hook(self, gltf2_scene, blender_scene)

    def gather_node_hook(self, gltf2_object, blender_object, _export_settings):
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_node_hook(self, gltf2_object, blender_object)

    def gather_gltf_hook(self, _active_scene_idx, _scenes, animations, _export_settings):
        if bpy.context.scene.panel_props.gltf_extension.is_exporting_with_goblend:
            _gather_gltf_hook(self, animations)


def _init(self):
    from io_scene_gltf2.io.com.gltf2_io_extensions import Extension, ChildOfRootExtension

    self.Extension = Extension
    self.ChildOfRootExtension = ChildOfRootExtension
    self.godot_scenes_dict = {}
    self.root_node = None
    self.blender_object_name_to_gltf_node = {}
    for godot_scene in bpy.context.scene.panel_props.gltf_extension.godot_scenes:
        self.godot_scenes_dict[godot_scene.object_name] = godot_scene


def _gather_gltf_extensions_hook(self, gltf2_plan):
    if gltf2_plan.extensions is None:
        gltf2_plan.extensions = {}

    gltf_extension = bpy.context.scene.panel_props.gltf_extension
    # add save paths
    paths = {}
    path_keys = gltf_extension.save_paths.paths()
    for path_key in path_keys:
        paths[path_key] = getattr(gltf_extension.save_paths, path_key)

    gltf2_plan.extensions[goblend_general] = self.Extension(
        name=goblend_general, extension={"save_paths": paths}, required=False
    )
    # need to add some arbitrary property for GODOT_single_root to be in extensions_used
    # since we set it to an empty array it won't be added in the "extensions" dict
    # but still be under "extensionsUsed"
    gltf2_plan.extensions[godot_single_root] = self.Extension(
        name=godot_single_root, extension={"foo": []}, required=False
    )

    # have to ensure that root node is at position 0
    if len(gltf2_plan.nodes) > 1 and gltf2_plan.nodes[0] != self.root_node:
        # make sure to place the root node at first place
        index_of_root_node = gltf2_plan.nodes.index(self.root_node)
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
                    if ext_name != "KHR_animation_pointer" or not "pointer" in ext:
                        continue
                    if ext["pointer"].startswith("/nodes/"):
                        node_idx = ext["pointer"][len("/nodes/") : ext["pointer"].index("/", len("/nodes/"))]
                        if node_idx == "0":
                            ext["pointer"] = "/nodes/" + str(index_of_root_node) + ext["pointer"][len("/nodes/0") :]
                        elif node_idx == str(index_of_root_node):
                            ext["pointer"] = "/nodes/0" + ext["pointer"][len("/nodes/" + str(index_of_root_node)) :]


def _gather_scene_hook(self, gltf2_scene, blender_scene):
    gltf_extension = blender_scene.panel_props.gltf_extension

    texture_group_dict = {}
    for texture_group in gltf_extension.texture_groups:
        for mat_name in texture_group.materials:
            texture_group_dict[mat_name.name] = texture_group.name

    materials = set()
    for node in gltf2_scene.nodes:
        if node.mesh:
            for primitive in node.mesh.primitives:
                if primitive.material:
                    materials.add(primitive.material)

    # iterate over all materials, if it belongs to a texture group rename it the first time and otherwise discard it
    material_dict = {}
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
        if not mat_name in material_dict:
            continue
        material_node = material_dict[mat_name]
        ext = {
            "transparency_mode": material.transparency_mode,
        }
        if material.transparency_mode == "SCISSOR":
            ext["transparency_alpha_scissor_threshold"] = material.transparency_alpha_scissor_threshold
        if material.shader_code != "":
            ext["shader_code"] = material.shader_code
            ext["shader_uniforms"] = []
            for uniform in material.shader_uniforms:
                ext["shader_uniforms"].append({"var_name": uniform.var_name, "uniform_data": uniform.uniform_data})
        ext["cull_mode"] = material.cull_mode
        material_node.extensions[goblend_material] = self.Extension(
            name=goblend_material,
            extension=ext,
            required=False,
        )

    # get physics types to distinguish between area shapes and body shapes
    physics_body_types = {}
    for physics_body in gltf_extension.physics_bodies:
        physics_body_types[physics_body.name] = physics_body.type

    # create shape nodes
    shapes_dict = {}
    for shape in gltf_extension.collision_shapes:
        gltf2_scene.nodes.remove(self.blender_object_name_to_gltf_node[shape.object.name])
        shape_node = None
        if shape.type == "box":
            shape_node = _add_box_shape(
                self,
                shape.object,
                physics_body_types[shape.parent_name] == "AREA",
                shape.dimensions[0],
                shape.dimensions[1],
                shape.dimensions[2],
            )
        elif shape.type == "cylinder":
            shape_node = _add_cylinder_shape(
                self,
                shape.object,
                physics_body_types[shape.parent_name] == "AREA",
                shape.radius,
                shape.height,
            )
        elif shape.type == "sphere":
            shape_node = _add_sphere_shape(
                self, shape.object, physics_body_types[shape.parent_name] == "AREA", shape.radius
            )
        elif shape.type == "convcol":
            shape_node = _add_convex_shape(
                self,
                shape.object,
                physics_body_types[shape.parent_name] == "AREA",
                self.blender_object_name_to_gltf_node[shape.object.name].mesh,
            )
        else:
            # unknown shape type
            log("Unknown shape type: " + shape.type, "WARNING")
            continue
        if next((b for b in gltf_extension.physics_bodies if b.name == shape.parent_name), None):
            if not shape.parent_name in shapes_dict:
                shapes_dict[shape.parent_name] = []
            shapes_dict[shape.parent_name].append(shape_node)
        else:
            # if the parent collection isn't a physics body (because it wasn't added as a setting) add the shape to the "Collisions" collection
            if not collisions_collection in shapes_dict:
                shapes_dict[collisions_collection] = []
            shapes_dict[collisions_collection].append(shape_node)
    root_physics_body_node = None
    for physics_body in gltf_extension.physics_bodies:
        if not physics_body.name in shapes_dict:
            # body has no shapes
            shapes_dict[physics_body.name] = []
        physics_body_types[physics_body.name] = physics_body.type
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
            # rename the root node to the filename
            physics_body_node.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            root_physics_body_node = physics_body_node
        # add node to the scene
        gltf2_scene.nodes.append(physics_body_node)
    children_of_root = []
    for node in gltf2_scene.nodes:
        if node != root_physics_body_node:
            children_of_root.append(node)
    # make the root node the only scene child and add the rest as children of that root node
    gltf2_scene.nodes = [root_physics_body_node]
    root_physics_body_node.children.extend(children_of_root)
    self.root_node = root_physics_body_node


def _gather_node_hook(self, gltf2_object, blender_object):
    scene = bpy.context.scene
    self.blender_object_name_to_gltf_node[blender_object.name] = gltf2_object
    if blender_object.name in self.godot_scenes_dict:
        # is godot scene
        if gltf2_object.extensions is None:
            gltf2_object.extensions = {}
        gltf2_object.extensions[goblend_godot_scene] = self.Extension(
            name=goblend_godot_scene,
            extension={
                "scene_path": self.godot_scenes_dict[blender_object.name].scene_path,
            },
            required=False,
        )
        gltf2_object.mesh = None
        return

    if gltf2_object.extensions and "KHR_lights_punctual" in gltf2_object.extensions:
        # it's a light
        light_settings = None
        for setting in scene.light_panel_props:
            if setting.light == blender_object:
                light_settings = setting
                break
        if not light_settings:
            return
        ext = {
            "omni_range": setting.omni_range,
            "omni_attenuation": setting.omni_attenuation,
            "omni_shadow_mode": int(setting.omni_shadow_mode),
            "spot_range": setting.spot_range,
            "spot_attenuation": setting.spot_attenuation,
            "spot_angle": setting.spot_angle,
            "spot_angle_attenuation": setting.spot_angle_attenuation,
            "light_color": [x for x in setting.light_color],
            "light_energy": setting.light_energy,
            "light_indirect_energy": setting.light_indirect_energy,
            "light_volumetric_fog_energy": setting.light_volumetric_fog_energy,
            "light_angular_distance": setting.light_angular_distance,
            "light_size": setting.light_size,
            "light_negative": setting.light_negative,
            "light_specular": setting.light_specular,
            "light_bake_mode": int(setting.light_bake_mode),
            "light_cull_mask": setting.light_cull_mask,
            "shadow_enabled": setting.shadow_enabled,
        }
        gltf2_object.extensions[goblend_light] = self.Extension(name=goblend_light, extension=ext, required=False)
        return

    for prop in scene.object_panel_props:
        if prop.enabled and prop.obj == blender_object:
            if gltf2_object.extensions is None:
                gltf2_object.extensions = {}
            gltf2_object.extensions[goblend_object] = self.Extension(
                name=goblend_object, extension={"shadow_cast_mode": prop.shadow_cast_mode}, required=False
            )
            break


def _gather_gltf_hook(self, animations):
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
        if anim_prop == None:
            continue
        ext = {"autoplay": anim_prop.autoplay, "loop": anim_prop.loop}
        if animation.extensions == None:
            animation.extensions = {}
        animation.extensions[goblend_animation] = self.Extension(name=goblend_animation, extension=ext, required=False)


def _get_middle_point(shapes):
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


def _create_node(name, extensions={}, translation=[0, 0, 0], children=[], rotation=None, scale=None):
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
        children=children,
        extras=None,
        mesh=None,
        scale=scale,
        skin=None,
        weights=None,
    )


def _create_physics_body(
    self,
    type,
    shape,
    name,
    is_area_shape=False,
    translation=[0, 0, 0],
    rotation=None,
    layers=None,
    masks=None,
    groups=None,
):
    ext = {}
    physics_body_ext = {}
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
    if not shape is None:
        if is_area_shape:
            physics_body_ext["trigger"] = {"shape": shape}
        else:
            physics_body_ext["collider"] = {"shape": shape}
    if physics_body_ext:
        ext[omi_physics_body] = self.Extension(name=omi_physics_body, extension=physics_body_ext, required=False)

    physics_body_attributes_ext = {}
    if not layers is None:
        physics_body_attributes_ext["layers"] = layers
    if not masks is None:
        physics_body_attributes_ext["masks"] = masks
    if not groups is None:
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


def _add_box_shape(self, obj, is_area_shape, dim_x, dim_y, dim_z):
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


def _add_cylinder_shape(self, obj, is_area_shape, radius, height):
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


def _add_sphere_shape(self, obj, is_area_shape, radius):
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


def _add_convex_shape(self, obj, is_area_shape, mesh):
    shape = self.ChildOfRootExtension(
        path=["shapes"], name=omi_physics_shape, extension={"type": "convex", "convex": {"mesh": mesh}}, required=False
    )
    return _create_shape_node(self, obj, shape, is_area_shape)


def _create_shape_node(self, obj, shape, is_area_shape):
    # swap y and z as godot uses y for up/down
    translation = [obj.location[0], obj.location[2], -obj.location[1]]
    rotation = None
    if obj.rotation_mode == "QUATERNION":
        rotation = [a for a in obj.rotation_quaternion]
    elif obj.rotation_mode == "AXIS_ANGLE":
        rotation = [a for a in Quaternion(obj.rotation_axis_angle[1:], obj.rotation_axis_angle[0])]
    else:
        rotation = [a for a in obj.rotation_euler.to_quaternion()]
    return _create_physics_body(
        self, None, shape, obj.name, is_area_shape=is_area_shape, translation=translation, rotation=rotation
    )
