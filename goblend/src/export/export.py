# export.py
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
import os
import subprocess

from .handle_materials import handle_materials, check_convert_to_shader
from .clean_up import first_clean_up, last_clean_up
from .setup import setup
from ..utils import get_root_dir


def handle_collision_shapes(collision_objects, paths):
    collision_shapes = bpy.context.scene.panel_props.gltf_extension.collision_shapes
    for val in collision_objects:
        obj = val[0]
        if "boxshape" in obj.name.lower():
            coll_shape = collision_shapes.add()
            coll_shape.type = "box"
            coll_shape.parent_name = val[1]
            coll_shape.object = obj
            coll_shape.dimensions = [obj.dimensions[0], obj.dimensions[1], obj.dimensions[2]]
        elif "cylshape" in obj.name.lower() or "cylindershape" in obj.name.lower():
            coll_shape = collision_shapes.add()
            coll_shape.type = "cylinder"
            coll_shape.parent_name = val[1]
            coll_shape.object = obj
            coll_shape.height = obj.dimensions[2]
            coll_shape.radius = obj.dimensions[0] / 2.0
        elif "sphereshape" in obj.name.lower():
            coll_shape = collision_shapes.add()
            coll_shape.type = "sphere"
            coll_shape.parent_name = val[1]
            coll_shape.object = obj
            coll_shape.radius = obj.dimensions[2] / 2.0
        else:
            coll_shape = collision_shapes.add()
            coll_shape.type = "convcol"
            coll_shape.parent_name = val[1]
            coll_shape.object = obj


def prep_for_export(
    objects, found_col_objects, collision_objects, collision_collection, settings_for_godot, godot_scene_nodes, paths
):
    # select all objects since we only export selected
    for obj in objects:
        obj.select_set(True)

    # and also select objects that hold the collections for external libraries
    # because we will later replace them with the scene instance in godot
    for obj in found_col_objects:
        obj.select_set(True)

    # handle collision objects
    handle_collision_shapes(collision_objects, paths)
    # also select them
    for val in collision_objects:
        val[0].select_set(True)

    # and select the godot_scene_nodes
    for obj in godot_scene_nodes:
        obj.select_set(True)

    gltf_extension = bpy.context.scene.panel_props.gltf_extension

    added_root_node = False

    if collision_collection != None:
        for sett in settings_for_godot["collisions"]:
            added_root_node = added_root_node or sett["collection"].name == "Collisions"
            physics_body = gltf_extension.physics_bodies.add()
            physics_body.name = sett["collection"].name
            physics_body.type = sett["type"]
            if sett["layer_overrides"] == None:
                for layer in settings_for_godot["default_collision_layers"]:
                    l = physics_body.layers.add()
                    l.value = int(layer)
            else:
                for layer in sett["layer_overrides"]:
                    l = physics_body.layers.add()
                    l.value = int(layer)

            if sett["mask_overrides"] == None:
                for mask in settings_for_godot["default_collision_masks"]:
                    m = physics_body.masks.add()
                    m.value = int(mask)
            else:
                for mask in sett["mask_overrides"]:
                    m = physics_body.masks.add()
                    m.value = int(mask)

            if sett["group_overrides"] == None:
                for group in settings_for_godot["default_groups"]:
                    g = physics_body.groups.add()
                    g.value = group
            else:
                for group in sett["group_overrides"]:
                    g = physics_body.groups.add()
                    g.value = group

    # add root node if it does not exist yet
    if not added_root_node:
        root_physics_body = gltf_extension.physics_bodies.add()
        root_physics_body.name = "Collisions"
        root_physics_body.type = settings_for_godot["default_physics_type"]
        for layer in settings_for_godot["default_collision_layers"]:
            l = root_physics_body.layers.add()
            l.value = int(layer)
        for mask in settings_for_godot["default_collision_masks"]:
            m = root_physics_body.masks.add()
            m.value = int(mask)
        for group in settings_for_godot["default_groups"]:
            g = root_physics_body.groups.add()
            g.value = group

    # finally also add lights
    for obj in bpy.data.objects:
        if obj.type == "LIGHT" and not obj.hide_render and obj.library == None:
            obj.hide_set(False)
            obj.select_set(True)


def export(
    godot_exec_path,
    texture_dim,
    uv_map_override,
    bake_margins,
    texture_groups,
    texture_overrides,
    settings_for_godot,
    paths,
):
    (
        objects,
        found_col_objects,
        collision_objects,
        collision_collection,
        export_path_glb,
        godot_scene_nodes,
        selected_objects,
        hidden_layer_collections,
        hidden_objects,
    ) = setup(texture_groups, settings_for_godot)
    (
        extra_shader_nodes,
        inputs,
        created_tex_nodes_per_mat_per_obj,
        old_meshes,
        orig_mod_per_obj,
        converted_mat_names,
        images_created,
    ) = handle_materials(
        uv_map_override,
        objects,
        paths,
        texture_groups,
        settings_for_godot,
        bake_margins,
        texture_dim,
        texture_overrides,
    )

    blend_path = os.path.normcase(bpy.data.filepath)
    filename = os.path.basename(blend_path)

    prep_for_export(
        objects,
        found_col_objects,
        collision_objects,
        collision_collection,
        settings_for_godot,
        godot_scene_nodes,
        paths,
    )

    check_convert_to_shader(settings_for_godot, converted_mat_names, objects)

    # export, apply remaining modifiers
    bpy.ops.export_scene.gltf(
        filepath=export_path_glb + os.path.splitext(filename)[0] + ".gltf",
        export_format="GLTF_SEPARATE",
        use_selection=True,
        export_lights=True,
        export_apply=True,
        export_keep_originals=True,
        export_animation_mode="NLA_TRACKS",
        export_pointer_animation=True,
        export_convert_animation_pointer=True,
    )

    first_clean_up(objects, extra_shader_nodes, inputs, created_tex_nodes_per_mat_per_obj, old_meshes, orig_mod_per_obj)

    # import into godot
    root_dir = get_root_dir()

    # this will also run post_import.gd which creates a copy of the project in a temporary folder
    subprocess.run([godot_exec_path, "--path", root_dir, "--headless", "--import"])
    last_clean_up(
        images_created,
        found_col_objects,
        collision_objects,
        export_path_glb,
        selected_objects,
        hidden_layer_collections,
        hidden_objects,
    )
