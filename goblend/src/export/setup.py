# setup.py
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

from typing import cast

from ..types.goblend_types import SettingsForGodot

from ..config import PathKeysStringVal, PathKeysBoolVal, Paths

from ..utils import get_root_dir

from ...src.log import log

save_path_keys: list[PathKeysStringVal] = [
    "scene_save_path",
    "material_save_path",
    "texture_save_path",
    "animation_library_save_path",
    "animation_save_path",
    "shader_save_path",
    "collision_shapes_save_path",
    "mesh_save_path",
]

save_path_uses_scene_name = [False, True, True, True, True, True, False, True]

save_path_hierarchy_keys: list[PathKeysBoolVal] = [
    "scene_use_same_hierarchy",
    "material_use_same_hierarchy",
    "texture_use_same_hierarchy",
    "animation_library_use_same_hierarchy",
    "animation_use_same_hierarchy",
    "shader_use_same_hierarchy",
    "reuse_collision_shapes",
    "mesh_use_same_hierarchy",
]


def find_objs_and_cols(
    root: bpy.types.Collection,
    found_col_objects: list[bpy.types.Object],
    seen_linked_collections: set[str],
    process_linked_collections: bool,
) -> bpy.types.Collection | None:
    collision_collection: bpy.types.Collection | None = None
    if root.name == bpy.context.scene.panel_props.collision_collection:
        collision_collection = root
    for child in root.children:
        coll = find_objs_and_cols(child, found_col_objects, seen_linked_collections, process_linked_collections)
        if coll is not None:
            collision_collection = coll
    for obj in root.objects:
        if obj.instance_type == "COLLECTION" and obj.instance_collection and not obj.hide_render:
            col = obj.instance_collection
            if col.library is not None:
                blender_binary_path = bpy.app.binary_path

                library_blend_file = os.path.normpath(os.path.abspath(bpy.path.abspath(col.library.filepath)))

                if not bpy.context.view_layer.objects.active:
                    # without an active object, the operator below will fail
                    bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode="OBJECT")
                bpy.ops.mesh.primitive_cube_add(location=obj.location, rotation=obj.rotation_euler)

                cube = cast(bpy.types.Object, bpy.context.active_object)
                cube.name = obj.name + "__tmp_name"
                cube.scale = obj.scale  # add scale after creating because otherwise it directly applies it

                found_col_objects.append(cube)

                collection_name = col.name.replace("'", "\\'")
                collection_identifier = col.library.filepath + collection_name

                if collection_identifier not in seen_linked_collections:
                    log("Found Library: " + col.library.name)
                    seen_linked_collections.add(collection_identifier)
                    if process_linked_collections:
                        subprocess.run(
                            [
                                blender_binary_path,
                                "-b",
                                "--addons",
                                "goblend",
                                library_blend_file,
                                "--python-expr",
                                "import bpy; bpy.context.scene.is_root_scene = False; bpy.context.scene.panel_props.linked_collection_identifier = '"
                                + collection_identifier
                                + "'; bpy.context.scene.panel_props.collection_name = '"
                                + collection_name
                                + "'; bpy.ops.scene.export_to_godot()",
                            ]
                        )
                    else:
                        subprocess.run(
                            [
                                blender_binary_path,
                                "-b",
                                "--addons",
                                "goblend",
                                library_blend_file,
                                "--python-expr",
                                "import bpy; bpy.context.scene.panel_props.linked_collection_identifier = '"
                                + collection_identifier
                                + "'; bpy.context.scene.panel_props.collection_name = '"
                                + collection_name
                                + "'; bpy.ops.scene.save_scene_in_tmp_file()",
                            ]
                        )
                tmp_file_path = os.path.normcase(os.path.join(get_root_dir(), ".tmp.goblend"))
                is_next = False
                scene_path = None
                with open(tmp_file_path, "r") as tmp_file:
                    for line in tmp_file:
                        if is_next:
                            scene_path = line.strip()
                            break
                        if line.startswith(collection_identifier):
                            is_next = True
                if scene_path:
                    godot_scene = bpy.context.scene.panel_props.gltf_extension.godot_scenes.add()
                    godot_scene.object_name = cube.name
                    godot_scene.scene_path = scene_path
                else:
                    log(
                        "Scene path not found for library: "
                        + library_blend_file
                        + ", with collection identifier: "
                        + collection_identifier,
                        "ERROR",
                    )

    return collision_collection


def get_objects_to_export(texture_groups: set[str]) -> tuple[list[bpy.types.Object], set[bpy.types.Object]]:
    objects: list[bpy.types.Object] = []
    hidden_objects: set[bpy.types.Object] = set()
    for obj in cast(bpy.types.Scene, bpy.context.scene).objects:
        # only export object if it's a mesh, not hidden from rendering and not from a library
        if obj.type == "MESH" and not obj.hide_render and obj.library is None and not obj.name.endswith("__tmp_name"):
            if obj.hide_get():
                hidden_objects.add(obj)
            obj.hide_set(False)  # make every object that we take into consideration visible
            objects.append(obj)
        else:
            continue

        for slot in obj.material_slots:
            for grp in texture_groups:
                if slot.material and slot.material.name == grp:
                    raise Exception(
                        "There is a material named" + slot.material.name + " which conflicts with a texture group name"
                    )
    return objects, hidden_objects


def get_collision_objects(
    collision_collection: bpy.types.Collection | None, objects: list[bpy.types.Object]
) -> set[tuple[bpy.types.Object, str]]:
    collision_objects: set[tuple[bpy.types.Object, str]] = set()
    if collision_collection is not None:

        def remove_collision_from_render(col: bpy.types.Collection) -> None:
            to_remove: set[bpy.types.Object] = set()
            for obj in col.objects:
                if obj in objects:
                    to_remove.add(obj)
            for obj in to_remove:
                objects.remove(obj)
                collision_objects.add((obj, col.name))

        remove_collision_from_render(collision_collection)
        for col in collision_collection.children_recursive:
            remove_collision_from_render(col)
    return collision_objects


def remove_godot_scene_objects(objects: list[bpy.types.Object]) -> set[bpy.types.Object]:
    # this is much slower than a simple bpy.data.collections.get("bpy.context.scene.panel_props.godot_scenes_collection"),
    # but it only includes collections of the current scene
    # it shouldn't matter too much with a low collection count
    scene: bpy.types.Scene | None = bpy.context.scene
    all_collections_in_scene = scene.collection.children_recursive if scene else []
    godot_scenes: bpy.types.Collection | None = None
    for coll in all_collections_in_scene:
        if coll.name == bpy.context.scene.panel_props.godot_scenes_collection:
            godot_scenes = coll
            break
    godot_scene_nodes: set[bpy.types.Object] = set()
    if not godot_scenes:
        return godot_scene_nodes
    to_remove: set[bpy.types.Object] = set()
    for obj in godot_scenes.objects:
        if obj in objects:
            to_remove.add(obj)
        log("Found Object to be replaced with Godot Scene: " + obj.name)
        godot_scene_nodes.add(obj)
    for obj in to_remove:
        objects.remove(obj)

    return godot_scene_nodes


def write_tmp_file(paths: Paths) -> None:
    root_dir = get_root_dir()

    # use temp file for storing paths of child scenes
    # will be read by by other instances of blender to figure out what scenes to link
    tmp_file_path = os.path.normcase(os.path.join(root_dir, ".tmp.goblend"))
    with open(tmp_file_path, "a") as tmp_file:
        tmp_file.write(
            bpy.context.scene.panel_props.linked_collection_identifier
            + "\n"
            + os.path.join(paths["scene_save_path"], bpy.context.scene.panel_props.gltf_extension.scene_name)
            + "\n"
        )


def setup(
    texture_group_assignments: dict[str, str],
    settings_for_godot: SettingsForGodot,
    process_linked_collections: bool,
    paths: Paths,
) -> tuple[
    list[bpy.types.Object],
    list[bpy.types.Object],
    set[tuple[bpy.types.Object, str]],
    bpy.types.Collection | None,
    str,
    set[bpy.types.Object],
    list[bpy.types.Object],
    set[bpy.types.LayerCollection],
    set[bpy.types.Object],
]:
    log("Running export for: " + os.path.normcase(bpy.data.filepath))

    write_tmp_file(paths)

    selected_objects = list(bpy.context.selected_objects)

    root_dir = get_root_dir()

    seen_linked_collections: set[str] = set()

    found_col_objects: list[bpy.types.Object] = []

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection

    collision_collection = find_objs_and_cols(
        bpy.context.scene.collection, found_col_objects, seen_linked_collections, process_linked_collections
    )

    for obj_name in settings_for_godot["godot_scenes"]:
        godot_scene = bpy.context.scene.panel_props.gltf_extension.godot_scenes.add()
        godot_scene.object_name = obj_name
        godot_scene.scene_path = settings_for_godot["godot_scenes"][obj_name]

    # make all LayerCollections visible
    # we need this to later make all objects visible and then to export the visible objects
    hidden_layer_collections: set[bpy.types.LayerCollection] = set()

    def loop_layer_collections(layer_coll: bpy.types.LayerCollection) -> None:
        if layer_coll.hide_viewport:
            hidden_layer_collections.add(layer_coll)
        layer_coll.hide_viewport = False
        for c in layer_coll.children:
            loop_layer_collections(c)

    loop_layer_collections(bpy.context.view_layer.layer_collection)  # this is the root collection

    texture_groups: set[str] = set()

    for val in texture_group_assignments.values():
        if val not in texture_groups:
            log("INFO: Found  " + val)
            texture_groups.add(val)

    objects, hidden_objects = get_objects_to_export(texture_groups)

    collision_objects = get_collision_objects(collision_collection, objects)

    godot_scene_nodes = remove_godot_scene_objects(objects)

    log("Collision Objects:\n" + str(collision_objects))

    scene = bpy.context.scene

    if scene.render.engine != "CYCLES":
        log("Render Engine is not set to cycles, baking won't work. Changing to Cycles", "WARNING")
        scene.render.engine = "CYCLES"
    if scene.render.image_settings.file_format != "PNG":
        log("Setting image settings: file_format to PNG, was: " + scene.render.image_settings.file_format)
        scene.render.image_settings.file_format = "PNG"
    if scene.render.image_settings.compression != 100:
        log("Setting image settings: compression to 100, was: " + str(scene.render.image_settings.compression))
        scene.render.image_settings.compression = 100
    if scene.render.image_settings.color_mode != "RGB":
        log("Setting image settings: color_mode to RGB, was: " + scene.render.image_settings.color_mode)
        scene.render.image_settings.color_mode = "RGB"
    if scene.render.image_settings.color_depth != "8":
        log("Setting image settings: color_depth to 8, was: " + scene.render.image_settings.color_depth)
        scene.render.image_settings.color_depth = "8"

    # create it again every time because it is deleted by the gdscript script
    export_path_glb = os.path.join(os.path.join(root_dir, "tmp_goblend_export"), "")
    os.makedirs(export_path_glb, exist_ok=True)
    log("Setup done")

    return (
        objects,
        found_col_objects,
        collision_objects,
        collision_collection,
        export_path_glb,
        godot_scene_nodes,
        selected_objects,
        hidden_layer_collections,
        hidden_objects,
    )
