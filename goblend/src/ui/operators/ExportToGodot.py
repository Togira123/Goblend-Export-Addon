import bpy
import os
import mathutils
import traceback

from ...config import abs_path, get_config
from ...export.export import export
from ...export.setup import save_path_keys, save_path_hierarchy_keys, save_path_uses_filename
from ...log import log
from .... import __package__ as base_package


class SCENE_OT_RootExportToGodot(bpy.types.Operator):
    bl_idname = "scene.root_export_to_godot"
    bl_label = "Export to Godot"
    bl_description = "Export all meshes in the current scene to Godot"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        log("------------ STARTING EXPORT ------------")
        context.scene.is_root_scene = True
        bpy.ops.scene.export_to_godot()
        return {"FINISHED"}


class SCENE_OT_ExportToGodot(bpy.types.Operator):
    bl_idname = "scene.export_to_godot"
    bl_label = "Export to Godot"
    bl_description = "Export all meshes in the current scene to Godot"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        props = scene.panel_props
        default_collision_props = scene.default_collision_panel_props
        addon_prefs = bpy.context.preferences.addons[base_package].preferences

        if addon_prefs.godot_file_path == "":
            log(
                "Please specify the path to the Godot Executable in the Add-on preferences (Edit > Preferences > Add-ons)",
                "ERROR",
            )
            self.report(
                {"ERROR_INVALID_INPUT"},
                "Please specify the path to the Godot Executable in the Add-on preferences (Edit > Preferences > Add-ons)",
            )
            return {"CANCELLED"}

        # reset all collection gltf properties
        props.gltf_extension.collision_shapes.clear()
        props.gltf_extension.physics_bodies.clear()
        props.gltf_extension.materials.clear()
        props.gltf_extension.texture_groups.clear()
        props.gltf_extension.godot_scenes.clear()

        texture_dim = {"x": props.texture_dim[0], "y": props.texture_dim[1]}

        uv_map_override = {}
        texture_groups = {}

        texture_overrides = {}

        bake_margins = {}

        config = get_config()

        default_layers = []
        seen = set()
        if default_collision_props.use_layer_config_value:
            for layer in config["defaults"]["collision_layers"]:
                l = str(layer)
                if not l in seen:
                    default_layers.append(l)
                    seen.add(l)
        else:
            for default_layer in default_collision_props.default_layers_list:
                if default_layer.enabled and not default_layer.layer in seen:
                    default_layers.append(default_layer.layer)
                    seen.add(default_layer.layer)

        default_masks = []
        seen = set()
        if default_collision_props.use_mask_config_value:
            for mask in config["defaults"]["collision_masks"]:
                m = str(mask)
                if not m in seen:
                    default_masks.append(m)
                    seen.add(m)
        else:
            for default_mask in default_collision_props.default_masks_list:
                if default_mask.enabled and not default_mask.mask in seen:
                    default_masks.append(default_mask.mask)
                    seen.add(default_mask.mask)

        default_groups = []
        seen = set()
        for default_group in default_collision_props.default_groups_list:
            if default_group.enabled and not default_group.group in seen:
                default_groups.append(default_group.group)
                seen.add(default_group.group)

        settings_for_godot = {
            "transparency_mode": props.default_transparency_mode,
            "scissor_value": props.default_transparency_alpha_scissor_threshold,
            "cull_mode": props.default_cull_mode,
            "default_collision_layers": default_layers,
            "default_collision_masks": default_masks,
            "default_groups": default_groups,
            "default_physics_type": default_collision_props.type,
            "collisions": [],
            "material_transparency_mode_overrides": {},
            "material_cull_mode_overrides": {},
            "use_shader_mats": {},
            "limit_uv_effect_normal": {},
            "shadow_cast_mode": {},
            "animations": {},
            "godot_scenes": {},
            "lights": {},
        }

        for item in scene.object_panel_props:
            if not item.enabled:
                continue
            if not item.obj:
                continue
            if item.uv_map_enabled:
                if item.uv_map_per_texture_enabled:
                    uv_map_override[item.obj.name] = {
                        "Base Color": item.uv_map_base_color,
                        "Metallic/Roughness": item.uv_map_metallic_roughness,
                        "Normal": item.uv_map_normal,
                        "obj": item.obj,
                    }
                else:
                    uv_map_override[item.obj.name] = {
                        "Base Color": item.uv_map,
                        "Metallic/Roughness": item.uv_map,
                        "Normal": item.uv_map,
                        "obj": item.obj,
                    }
            settings_for_godot["shadow_cast_mode"][item.obj.name] = item.shadow_cast_mode

        gltf_texture_groups = {}
        for mat in scene.material_panel_props:
            if not mat.mat:
                continue

            if mat.override_texture_size:
                texture_overrides[mat.mat.name] = [mat.texture_dim[0], mat.texture_dim[1]]

            if mat.transparency_mode != "DEFAULT":
                settings_for_godot["material_transparency_mode_overrides"][mat.mat.name] = {
                    "mode": mat.transparency_mode,
                    "scissor": mat.transparency_alpha_scissor_threshold,
                }
            if mat.cull_mode != "DEFAULT":
                settings_for_godot["material_cull_mode_overrides"][mat.mat.name] = mat.cull_mode
            if mat.use_shader:
                settings_for_godot["use_shader_mats"][
                    mat.mat.name
                ] = None  # object, will be set when iterating over materials
            else:
                if mat.texture_group != "":
                    if not mat.texture_group in gltf_texture_groups:
                        gltf_texture_groups[mat.texture_group] = props.gltf_extension.texture_groups.add()
                        gltf_texture_groups[mat.texture_group].name = mat.texture_group
                    m = gltf_texture_groups[mat.texture_group].materials.add()
                    m.name = mat.mat.name
                    texture_groups[mat.mat.name] = mat.texture_group
                if mat.override_bake_margin:
                    bake_margins[mat.mat.name] = mat.bake_margin

            if mat.limit_uv_effect_normal:
                settings_for_godot["limit_uv_effect_normal"][mat.mat.name] = {
                    "min_x": mat.limit_uv_effect_normal_x_min,
                    "max_x": mat.limit_uv_effect_normal_x_max,
                    "min_y": mat.limit_uv_effect_normal_y_min,
                    "max_y": mat.limit_uv_effect_normal_y_max,
                    "obj": None,  # object, will be set when iterating over materials
                }

        for item in scene.collision_panel_props:
            if item.collection == None:
                continue
            obj = {
                "collection": item.collection,
                "type": item.type,
                "layer_overrides": None,
                "mask_overrides": None,
                "group_overrides": None,
            }
            if item.layers_override_enabled:
                seen = set()
                layers = []
                for layer_override in item.layers_override_list:
                    if layer_override.enabled and not layer_override.layer in seen:
                        layers.append(layer_override.layer)
                        seen.add(layer_override.layer)
                obj["layer_overrides"] = layers
            if item.masks_override_enabled:
                seen = set()
                masks = []
                for mask_override in item.masks_override_list:
                    if mask_override.enabled and not mask_override.mask in seen:
                        masks.append(mask_override.mask)
                        seen.add(mask_override.mask)
                obj["mask_overrides"] = masks
            if item.groups_override_enabled:
                seen = set()
                groups = []
                for group_override in item.groups_override_list:
                    if group_override.enabled and not group_override.group in seen:
                        groups.append(group_override.group)
                        seen.add(group_override.group)
                obj["group_overrides"] = groups

            settings_for_godot["collisions"].append(obj)

        for item in scene.animation_panel_props:
            if item.animation == None:
                continue
            settings_for_godot["animations"][item.animation.name] = {"autoplay": item.autoplay, "loop": item.loop}

        for item in scene.godot_scene_panel_props:
            if item.obj == None:
                continue
            scene_path = ""
            for godot_scene in config["godot_scenes"]:
                if godot_scene["name"] == item.scene:
                    scene_path = godot_scene["godot_scene_path"]
                    break
            if scene_path == "":
                log("Ignoring Godot Scene with name " + item.scene + ", not found in config", "WARNING")
                continue
            settings_for_godot["godot_scenes"][item.obj.name] = scene_path

        for item in scene.light_panel_props:
            if not item.light:
                continue
            settings_for_godot["lights"][item.light.name] = {}
            light_props = [
                "omni_range",
                "omni_attenuation",
                "omni_shadow_mode",
                "spot_range",
                "spot_attenuation",
                "spot_angle",
                "spot_angle_attenuation",
                "light_color",
                "light_energy",
                "light_indirect_energy",
                "light_volumetric_fog_energy",
                "light_angular_distance",
                "light_size",
                "light_negative",
                "light_specular",
                "light_bake_mode",
                "light_cull_mask",
                "shadow_enabled",
            ]
            for prop in light_props:
                value = getattr(item, prop)
                if type(value) is str or type(value) is int or type(value) is float:
                    settings_for_godot["lights"][item.light.name][prop] = str(value)
                elif type(value) is bool:
                    settings_for_godot["lights"][item.light.name][prop] = "true" if value else "false"
                elif type(value) is list:
                    settings_for_godot["lights"][item.light.name][prop] = map(str, value)
                elif type(value) is mathutils.Color:
                    settings_for_godot["lights"][item.light.name][prop] = [str(value.r), str(value.g), str(value.b)]
                else:
                    raise Exception("Unsupported type in light properties")

        paths = config["defaults"]["paths"].copy()
        if props.same_hierarchy_target.lower() != "default":
            paths["same_hierarchy_target"] = props.same_hierarchy_target

        for path_key in save_path_keys:
            if getattr(props, path_key).lower() != "default":
                paths[path_key] = abs_path(getattr(props, path_key))

        for path_key in save_path_hierarchy_keys:
            if getattr(props, path_key) != "DEFAULT":
                paths[path_key] = True if getattr(props, path_key) == "YES" else False

        hierarchy_key_array = []
        for save_hierarchy in save_path_hierarchy_keys:
            hierarchy_key_array.append(save_hierarchy)

        blend_path = os.path.normcase(bpy.data.filepath)

        hierarchy_path_start = blend_path.index(paths["same_hierarchy_target"]) + len(paths["same_hierarchy_target"])
        # remove forward and backward slashes from the beginning of the path
        hierarchy_path = blend_path[hierarchy_path_start : len(blend_path) - len(os.path.basename(blend_path))].lstrip(
            "/\\"
        )
        log("Hierarchy path: " + hierarchy_path)

        idx = 0
        for save_path in save_path_keys:
            if save_path == "collision_shapes_save_path":
                continue  # this is the exception, has no use hierarchy setting
            path = paths[save_path]
            if paths[hierarchy_key_array[idx]]:
                # append path
                path = os.path.join(os.path.normcase(path), hierarchy_path)
            if save_path_uses_filename[idx]:
                path = os.path.join(os.path.normcase(path), os.path.splitext(os.path.basename(blend_path))[0])
            paths[save_path] = abs_path(path)
            idx += 1

        whether_to_save_separately_keys = [
            "save_material_separately",
            "save_animation_library_separately",
            "save_animation_separately",
            "save_shader_separately",
        ]

        whether_to_save_separately_path_prop = [
            "material_save_path",
            "animation_library_save_path",
            "animation_save_path",
            "shader_save_path",
        ]

        for key in whether_to_save_separately_keys:
            if getattr(props, key) != "DEFAULT":
                paths[key] = True if getattr(props, key) == "YES" else False

        for key, path in zip(whether_to_save_separately_keys, whether_to_save_separately_path_prop):
            if not paths[key]:
                paths[path] = ""

        if not paths["reuse_collision_shapes"]:
            paths["collision_shapes_save_path"] = ""

        try:
            props.gltf_extension.is_exporting_with_goblend = True
            export(
                addon_prefs.godot_file_path,
                texture_dim,
                uv_map_override,
                bake_margins,
                texture_groups,
                texture_overrides,
                settings_for_godot,
                paths,
            )
            props.gltf_extension.is_exporting_with_goblend = False
            if scene.is_root_scene:
                log("------------ EXPORT DONE ------------")
            else:
                log("Sub-export done")
        except Exception as e:
            props.gltf_extension.is_exporting_with_goblend = False
            log(traceback.format_exc(), "ERROR")
            log(
                "An error happend while trying to export. Check the logs above for more info. If you believe this is a bug, read the docs first. If you are fairly certain it still is, feel free to open an issue.",
                "ERROR",
            )

            def draw_error(self, _context):
                self.layout.label(
                    text="Undo (Ctrl/Cmd + z) to return to your previous state. Check the log file for more details. If there is no log file, make sure to enable it in the addon preferences"
                )

            bpy.context.window_manager.popup_menu(draw_error, title="An Error happened", icon="ERROR")
        return {"FINISHED"}
