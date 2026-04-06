@tool
class_name GLTFDocumentExtensionEXTGoblendGeneral extends GLTFDocumentExtension

var ext_name := "EXT_goblend_general"

func _import_preflight(state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP

func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([ext_name])

func _import_post(state: GLTFState, root: Node) -> Error:
	if not state.json["extensions"].has(ext_name):
		return ERR_INVALID_DATA
	var ext: Dictionary = state.json["extensions"][ext_name]["save_paths"]
	if not ext.has("scene_save_path"):
		return ERR_INVALID_DATA

	var material_save_path: String = ext["material_save_path"] if ext.has("material_save_path") else ""
	var shader_save_path: String = ext["shader_save_path"] if ext.has("shader_save_path") else ""
	var seen_mats := PackedStringArray()
	Goblend.log_msg("Saving materials externally...")
	save_materials_externally(root, material_save_path, seen_mats, shader_save_path)
	
	var animation_save_path: String = ext["animation_save_path"] if ext.has("animation_save_path") else ""
	var animation_library_save_path: String = ext["animation_library_save_path"] if ext.has("animation_library_save_path") else ""
	
	handle_animation_player(root, animation_save_path, animation_library_save_path, root.name)

	save_collision_shapes_externally(root, ext["collision_shapes_save_path"] if ext.has("collision_shapes_save_path") else "")

	var mesh_save_path: String = ext["mesh_save_path"] if ext.has("mesh_save_path") else ""

	save_meshes_externally(root, mesh_save_path)

	var scene_save_path: String = ext["scene_save_path"]
	
	var scene := PackedScene.new()
	scene.pack(root)
	if not DirAccess.dir_exists_absolute(scene_save_path):
		DirAccess.make_dir_recursive_absolute(scene_save_path)
	ResourceSaver.save(scene, scene_save_path.path_join(root.name + ".tscn"))

	return OK

func save_materials_externally(root: Node, path: String, seen_mats: PackedStringArray, shader_path: String) -> void:
	if root is MeshInstance3D:
		var mesh: Mesh = root.mesh
		var surface_count := mesh.get_surface_count()
		for i in surface_count:
			var mat := mesh.surface_get_material(i)
			var mat_name := mat.resource_name
			if mat_name == "":
				continue
			var mat_path := path.path_join(mat_name + ".tres")
			if not seen_mats.has(mat_name):
				seen_mats.append(mat_name)
				if mat is ShaderMaterial:
					if shader_path != "":
						# also save the shader separately
						var shader_save_path := shader_path.path_join(mat_name + ".gdshader")
						if not DirAccess.dir_exists_absolute(shader_path):
							DirAccess.make_dir_recursive_absolute(shader_path)
						var ok := ResourceSaver.save(mat.shader, shader_save_path, ResourceSaver.FLAG_CHANGE_PATH)
						if ok == OK:
							Goblend.log_msg("Successfully saved shader at " + shader_save_path)
							mat.shader = load(shader_save_path)
						else:
							Goblend.log_msg("Failed to save shader at " + shader_save_path, "WARNING")
					else:
						Goblend.log_msg("Skip saving shader " + mat.shader.resource_name + " separately")
				if path != "":
					if not DirAccess.dir_exists_absolute(path):
						DirAccess.make_dir_recursive_absolute(path)
					var ok := ResourceSaver.save(mat, mat_path, ResourceSaver.FLAG_CHANGE_PATH)
					if ok != OK:
						Goblend.log_msg("Failed to save material at " + mat_path, "WARNING")
						continue
					Goblend.log_msg("Successfully saved material at " + mat_path)
				else:
					Goblend.log_msg("Skip saving material " + mat_name + " separately")
			if path != "":
				mesh.surface_set_material(i, load(mat_path))
	for child in root.get_children():
		save_materials_externally(child, path, seen_mats, shader_path)

func handle_animation_player(root: Node, animations_path: String, animation_libraries_path: String, lib_name: String) -> AnimationPlayer:
	var children := root.get_children()
	var anim_player: AnimationPlayer = null
	for child in children:
		if child is AnimationPlayer:
			anim_player = child
			var list: PackedStringArray = anim_player.get_animation_list()
			var library := AnimationLibrary.new()
			for name in list:
				var anim: Animation = anim_player.get_animation(name)
				for i in anim.get_track_count():
					anim.track_set_imported(i, false)
				if animations_path != "":
					if not DirAccess.dir_exists_absolute(animations_path):
						DirAccess.make_dir_recursive_absolute(animations_path)
					var ok := ResourceSaver.save(anim, animations_path + name + ".res", ResourceSaver.FLAG_CHANGE_PATH)
					if ok == OK:
						Goblend.log_msg("Successfully saved animation at " + animations_path + name + ".res")
						anim = load(animations_path + name + ".res")
					else:
						Goblend.log_msg("Failed to save animation at " + animations_path + name + ".res", "WARNING")
				else:
					Goblend.log_msg("Skip saving animation " + name + " separately")
				library.add_animation(name, anim)
			if animation_libraries_path != "":
				if not DirAccess.dir_exists_absolute(animation_libraries_path):
					DirAccess.make_dir_recursive_absolute(animation_libraries_path)
				var ok := ResourceSaver.save(library, animation_libraries_path + lib_name + ".res", ResourceSaver.FLAG_CHANGE_PATH)
				if ok == OK:
					Goblend.log_msg("Successfully saved animation library at " + animation_libraries_path + lib_name + ".res")
					library = load(animation_libraries_path + lib_name + ".res")
				else:
					Goblend.log_msg("Failed to save animation library at " + animation_libraries_path + lib_name + ".res", "WARNING")
			else:
				Goblend.log_msg("Skip saving animation library " + lib_name + " separately")
			# remove old libraries
			var old_library_list := anim_player.get_animation_library_list()
			for old_library in old_library_list:
				anim_player.remove_animation_library(old_library)
			anim_player.add_animation_library(lib_name, library)
			break
	# we only support one animation player per scene!
	if anim_player != null:
		return anim_player
	for child in children:
		anim_player = handle_animation_player(child, animations_path, animation_libraries_path, lib_name)
		if anim_player != null:
			return anim_player
	return null

func save_collision_shapes_externally(root: Node, path: String) -> void:
	if path == "":
		Goblend.log_msg("Skip saving collision shapes separately")
		return
	if root is CollisionShape3D:
		var shape: Shape3D = root.shape
		var shape_base_path := ""
		var shape_path := ""
		if shape is BoxShape3D:
			var dim_x_str := convert_to_rounded_float_str(shape.size.x)
			var dim_y_str := convert_to_rounded_float_str(shape.size.y)
			var dim_z_str := convert_to_rounded_float_str(shape.size.z)
			var shape_name := dim_x_str + "_" + dim_y_str + "_" + dim_z_str
			shape_base_path = path.path_join("boxshapes")
			shape_path = path.path_join("boxshapes".path_join(shape_name + ".tres"))
		elif shape is CylinderShape3D:
			var height_str := convert_to_rounded_float_str(shape.height)
			var radius_str := convert_to_rounded_float_str(shape.radius)
			var shape_name := height_str + "_" + radius_str
			shape_base_path = path.path_join("cylshapes")
			shape_path = path.path_join("cylshapes".path_join(shape_name + ".tres"))
		elif shape is SphereShape3D:
			var radius_str := convert_to_rounded_float_str(shape.radius)
			shape_base_path = path.path_join("sphereshapes")
			shape_path = path.path_join("sphereshapes".path_join(radius_str + ".tres"))
		if shape_path != "":
			if not ResourceLoader.exists(shape_path):
				if not DirAccess.dir_exists_absolute(shape_base_path):
					DirAccess.make_dir_recursive_absolute(shape_base_path)
				var ok := ResourceSaver.save(shape, shape_path, ResourceSaver.FLAG_CHANGE_PATH)
				if ok == OK:
					Goblend.log_msg("Successfully saved collision shape at " + shape_path)
				else:
					Goblend.log_msg("Failed to save collision shape at " + shape_path, "WARNING")
			root.shape = load(shape_path)
	for child in root.get_children():
		save_collision_shapes_externally(child, path)


func convert_to_rounded_float_str(f: float, precision := 1_000_000) -> String:
	var rounded := roundi(f * precision)
	var s := str(rounded)
	if s.length() < 7:
		s = "0." + "0".repeat(6 - s.length()) + s
	else:
		s = s.substr(0, s.length() - 6) + "." + s.substr(s.length() - 6)
	s += "000000000" # make sure the string is at least 9 characters long
	return s.substr(0, 9)

func save_meshes_externally(root: Node, path: String) -> void:
	if path == "":
		Goblend.log_msg("Skip saving meshes separately")
		return
	if root is MeshInstance3D:
		var mesh: Mesh = root.mesh
		var mesh_path := path.path_join(mesh.resource_name + ".res")
		if not DirAccess.dir_exists_absolute(path):
			DirAccess.make_dir_recursive_absolute(path)
		var ok := ResourceSaver.save(mesh, mesh_path, ResourceSaver.FLAG_CHANGE_PATH)
		if ok == OK:
			Goblend.log_msg("Successfully saved mesh at " + mesh_path)
			root.mesh = load(mesh_path)
		else:
			Goblend.log_msg("Failed to save mesh at " + mesh_path, "WARNING")
	for child in root.get_children():
		save_meshes_externally(child, path)
