@tool
extends EditorScenePostImport

var args: PackedStringArray
var scene: Node3D

var seen := {}

const SAVE_PATH_KEYS := [
	"scene_save_path",
	"material_save_path", 
	"texture_save_path",
	"animation_library_save_path",
	"animation_save_path",
	"shader_save_path",
	"collision_shapes_save_path"
]

var paths: Dictionary[String, String] = {}

func log_msg(message: String, type := "INFO"):
	var msg := type + ": " + str(message)
	var now := Time.get_time_dict_from_system()
	msg = ("[%02d:%02d:%02d] (GODOT) " % [now["hour"], now["minute"], now["second"]]) + msg
	var log_file := FileAccess.open("res://goblend.log", FileAccess.READ_WRITE)
	log_file.seek_end()
	log_file.store_string(msg + "\n")
	log_file.close()
	print(msg)

func _post_import(orig_scene: Node):
	args = OS.get_cmdline_user_args()
	if args.size() > 0 and args[0] == "true":
		log_msg("Executing post import")
		var root = StaticBody3D.new()
		root.name = orig_scene.name
		root.collision_layer = 1
		root.collision_mask = 0
		root.input_ray_pickable = false
		for child in orig_scene.get_children():
			operate(child, root, root)
		var s = PackedScene.new()
		var res = s.pack(root)
		if res == OK:
			if not DirAccess.dir_exists_absolute("res://tmp_goblend_export/"):
				DirAccess.make_dir_recursive_absolute("res://tmp_goblend_export/")
			ResourceSaver.save(s, "res://tmp_goblend_export/Tmp.tscn")
		root.free()
		run_import(1)
	return orig_scene

func operate(node: Node, parent: Node, root):
	if node != null:
		var n: Node
		if node is MeshInstance3D:
			n = MeshInstance3D.new()
			parent.add_child(n)
			n.owner = root
			n.name = node.name
			n.transform = node.transform
			n.mesh = node.mesh.duplicate(true)
		elif node is OmniLight3D:
			n = node.duplicate()
			parent.add_child(n)
			n.owner = root
			n.name = node.name
		elif node is SpotLight3D:
			n = node.duplicate()
			parent.add_child(n)
			n.owner = root
			n.name = node.name
		elif node is DirectionalLight3D:
			n = node.duplicate()
			parent.add_child(n)
			n.owner = root
			n.name = node.name
		elif node is StaticBody3D:
			# staticbodies can only be created if a collision shape
			# in blender has no specific type and hence a -convcolonly
			# suffix is appended to it which leads godot to create the
			# static body
			# we want to remove the static body but keep the collision shapes
			for child in node.get_children():
				if child is CollisionShape3D:
					n = child.duplicate()
					parent.add_child(n)
					n.owner = root
					n.name = node.name
					n.position = node.position + child.position
		elif node is CollisionShape3D:
			# same argument here
			# they should be reparented by the code above so no need
			# to do anything more with them
			pass
		elif node is AnimationPlayer:
			n = node.duplicate()
			parent.add_child(n)
			n.owner = root
			n.name = node.name
		elif node is Node3D:
			n = Node3D.new()
			parent.add_child(n)
			n.owner = root
			n.name = node.name
			n.transform = node.transform
		for child in node.get_children():
			operate(child, n, root)

func run_import(ind: int):
	scene = load("res://tmp_goblend_export/Tmp.tscn").instantiate()
	
	for save_path in SAVE_PATH_KEYS:
		var path := args[ind]
		ind += 1
		paths[save_path] = path
	
	ind = handle_collision_settings(ind)
	
	ind = handle_collision_shapes(ind)
	
	var blender_to_actual_mat_name := {}
	
	# apply materials
	var is_root_scene := true if args[ind].to_lower() == "true" else false
	var number_of_objects := int(args[ind + 1])
	var file_name := args[ind + 2]
	ind += 3
	for i in number_of_objects:
		var object_name := args[ind].validate_node_name()
		var number_of_material_slots := int(args[ind + 1])
		var shadow_cast_mode := args[ind + 2]
		var setting: GeometryInstance3D.ShadowCastingSetting
		match shadow_cast_mode:
			"OFF":
				setting = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			"ON":
				setting = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
			"DOUBLE_SIDED":
				setting = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
			"SHADOWS_ONLY":
				setting = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		ind += 3
		
		var node := find_node(scene, object_name)
		if node == null:
			log_msg("Node with name '" + object_name + "' not found!", "ERROR")
			# trigger an error
			var _tmp = node.material
			continue
		
		node.cast_shadow = setting
		
		for j in number_of_material_slots:
			var material_name := args[ind]
			var actual_material_name := args[ind]
			log_msg(material_name + " at " + str(j))
			var transparency_mode := args[ind + 1]
			var scissor_value: float
			if transparency_mode == "SCISSOR":
				ind += 1
				scissor_value = float(args[ind + 1])
			
			var cull_mode := args[ind + 2]
			
			var texture_group := args[ind + 3]
			var is_in_texture_group := texture_group != "null"
			if is_in_texture_group:
				material_name = texture_group 
			
			blender_to_actual_mat_name[actual_material_name] = material_name
			var number_of_connected_ports := int(args[ind + 4])
			ind += 5
			var material_location: String = paths["material_save_path"] + material_name + ".tres"
			if not DirAccess.dir_exists_absolute(paths["material_save_path"]):
				DirAccess.make_dir_recursive_absolute(paths["material_save_path"])
			
			var tex_dict := {}
			for k in number_of_connected_ports:
				var type := args[ind]
				var img_tex_file_name := args[ind + 1]
				var rgb_channel := args[ind + 2]
				tex_dict[type] = {
					"file": img_tex_file_name,
					"channel": rgb_channel
				}
				ind += 3
			
			var material: Material = node.mesh.surface_get_material(j)
			if not material is StandardMaterial3D:
				log_msg("Materials other than StandardMaterial3D are not supported! (" + material_name + ")", "ERROR")
				# trigger an error
				var _tmp = material.albedo_color
				continue

			# check whether that material already exists
			# but use a flag to make sure it is overridden at first
			if FileAccess.file_exists(material_location):
				if material_location in seen:
					log_msg("Material '" + material_name + "' seems to already exist, reusing for object " + object_name)
					node.mesh.surface_set_material(j, load(material_location))
					continue
				else:
					# remove the material
					DirAccess.remove_absolute(material_location)
			seen[material_location] = true

			if material.transparency != BaseMaterial3D.Transparency.TRANSPARENCY_DISABLED:
				# material is transparent
				match transparency_mode:
					"ALPHA":
						material.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA
					"SCISSOR":
						material.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA_SCISSOR
						material.alpha_scissor_threshold = scissor_value
					"HASH":
						material.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA_HASH
					"DEPTH_PRE_PASS":
						material.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
					_:
						log_msg("Unrecognized transparency mode received: " + transparency_mode, "WARNING")
			
			match cull_mode:
				"DISABLED":
					material.cull_mode = BaseMaterial3D.CullMode.CULL_DISABLED
				"BACK":
					material.cull_mode = BaseMaterial3D.CullMode.CULL_BACK
				"FRONT":
					material.cull_mode = BaseMaterial3D.CullMode.CULL_FRONT
			
			var tex_base_bath := paths["texture_save_path"]
			
			if "Base Color" in tex_dict:
				material.albedo_texture = load(tex_base_bath + tex_dict["Base Color"].file)
			else:
				material.albedo_texture = null
			
			if "Metallic" in tex_dict:
				material.metallic_texture = load(tex_base_bath + tex_dict["Metallic"].file)
				material.metallic_texture_channel = rgb_channel_to_flag(tex_dict["Metallic"].channel)
			else:
				material.metallic_texture = null
			if "Roughness" in tex_dict:
				material.roughness_texture = load(tex_base_bath + tex_dict["Roughness"].file)
				material.roughness_texture_channel = rgb_channel_to_flag(tex_dict["Roughness"].channel)
			else:
				material.roughness_texture = null
			
			if "Normal" in tex_dict:
				material.normal_texture = load(tex_base_bath + tex_dict["Normal"].file)
			else:
				material.normal_enabled = false
				material.normal_texture = null
			
			if "Transmission" in tex_dict:
				if tex_dict["Transmission"].file.is_valid_float():
					# it's just a value
					var val: float = tex_dict["Transmission"].file.to_float()
					if val > 0.0:
						# to enable the transmission effect in godot, we need to enable refraction on the material
						material.refraction_enabled = true
						material.refraction_scale = 0.0
			
			if is_in_texture_group:
				material.resource_name = material_name
				node.mesh.surface_set_name(j, material_name)
				# otherwise it already has the correct name
			
			var ok := ResourceSaver.save(material, material_location, ResourceSaver.FLAG_CHANGE_PATH)
			if ok == Error.OK:
				log_msg("successfully saved " + material_location)
				material = load(material_location)
				node.mesh.surface_set_material(j, material)
		
	var anim_player := handle_animation_player(scene, paths["animation_save_path"], paths["animation_library_save_path"], file_name)
	# material animations
	ind = handle_material_animations(ind, anim_player, file_name, blender_to_actual_mat_name)
	
	ind = handle_shaders(ind, blender_to_actual_mat_name)
	
	ind = handle_light_settings(ind)
	
	# add scene instances
	ind = instantiate_child_scenes(ind)
	
	var s := PackedScene.new()
	var res := s.pack(scene)
	
	if res == OK:
		if not DirAccess.dir_exists_absolute(paths["scene_save_path"]):
			
			DirAccess.make_dir_recursive_absolute(paths["scene_save_path"])
		
		ResourceSaver.save(s, paths["scene_save_path"] + file_name + ".tscn")
	
	free_node_and_children(scene)
	
	if is_root_scene:
		DirAccess.remove_absolute("res://.tmp.goblend")

func handle_collision_shapes(ind: int) -> int:
	var number_of_coll_shapes := int(args[ind])
	ind += 1
	for i in number_of_coll_shapes:
		var node_name := args[ind].validate_node_name()
		var type := args[ind + 1]
		ind += 2
		var node := find_node(scene, node_name)
		if node == null:
			log_msg("Node " + node_name + " not found when looking for collision shape", "ERROR")
			# trigger error by setting property on null value
			node.position.x = 0.0
		var position := node.position
		var rotation := node.rotation
		var parent := node.get_parent()
		parent.remove_child(node)
		free_node_and_children(node)
		if type == "box":
			var dim_x := float(args[ind])
			# switch y and z because blender uses z for height
			var dim_z := float(args[ind + 1])
			var dim_y := float(args[ind + 2])
			ind += 3
			var dim_x_str := convert_to_rounded_float_str(dim_x)
			var dim_y_str := convert_to_rounded_float_str(dim_y)
			var dim_z_str := convert_to_rounded_float_str(dim_z)
			var shape_name := dim_x_str + "_" + dim_y_str + "_" + dim_z_str
			var shape_path := paths["collision_shapes_save_path"] + "boxshapes/" + shape_name + ".tres"
			var exists := ResourceLoader.exists(shape_path)
			var shape: BoxShape3D
			if exists:
				shape = load(shape_path)
			else:
				if not DirAccess.dir_exists_absolute(paths["collision_shapes_save_path"] + "boxshapes/"):
					DirAccess.make_dir_recursive_absolute(paths["collision_shapes_save_path"] + "boxshapes/")
				shape = BoxShape3D.new()
				shape.size = Vector3(dim_x, dim_y, dim_z)
				var ok := ResourceSaver.save(shape, shape_path, ResourceSaver.FLAG_CHANGE_PATH)
				if ok == Error.OK:
					log_msg("Successfully saved BoxShape3D " + shape_name + " to " + shape_path)
				shape = load(shape_path)
			var collision_shape := CollisionShape3D.new()
			collision_shape.shape = shape
			parent.add_child(collision_shape)
			collision_shape.owner = scene
			collision_shape.name = node_name
			collision_shape.position = position
			collision_shape.rotation = rotation
		elif type == "cyl":
			var height := float(args[ind])
			var radius := float(args[ind + 1])
			ind += 2
			var height_str := convert_to_rounded_float_str(height)
			var radius_str := convert_to_rounded_float_str(radius)
			var shape_name := height_str + "_" + radius_str
			var shape_path := paths["collision_shapes_save_path"] + "cylshapes/" + shape_name + ".tres"
			var exists := ResourceLoader.exists(shape_path)
			var shape: CylinderShape3D
			if exists:
				shape = load(shape_path)
			else:
				if not DirAccess.dir_exists_absolute(paths["collision_shapes_save_path"] + "cylshapes/"):
					DirAccess.make_dir_recursive_absolute(paths["collision_shapes_save_path"] + "cylshapes/")
				shape = CylinderShape3D.new()
				shape.height = height
				shape.radius = radius
				var ok := ResourceSaver.save(shape, shape_path, ResourceSaver.FLAG_CHANGE_PATH)
				if ok == Error.OK:
					log_msg("Successfully saved CylinderShape3D " + shape_name + " to " + shape_path)
				shape = load(shape_path)
			var collision_shape := CollisionShape3D.new()
			collision_shape.shape = shape
			parent.add_child(collision_shape)
			collision_shape.owner = scene
			collision_shape.name = node_name
			collision_shape.position = position
			collision_shape.rotation = rotation
		elif type == "sphere":
			var radius := float(args[ind])
			ind += 1
			var radius_str := convert_to_rounded_float_str(radius)
			var shape_name := radius_str
			var shape_path := paths["collision_shapes_save_path"] + "sphereshapes/" + shape_name + ".tres"
			var exists := ResourceLoader.exists(shape_path)
			var shape: SphereShape3D
			if exists:
				shape = load(shape_path)
			else:
				if not DirAccess.dir_exists_absolute(paths["collision_shapes_save_path"] + "sphereshapes/"):
					DirAccess.make_dir_recursive_absolute(paths["collision_shapes_save_path"] + "sphereshapes/")
				shape = SphereShape3D.new()
				shape.radius = radius
				var ok := ResourceSaver.save(shape, shape_path, ResourceSaver.FLAG_CHANGE_PATH)
				if ok == Error.OK:
					log_msg("Successfully saved SphereShape3D " + shape_name + " to " + shape_path)
				shape = load(shape_path)
			var collision_shape := CollisionShape3D.new()
			collision_shape.shape = shape
			parent.add_child(collision_shape)
			collision_shape.owner = scene
			collision_shape.name = node_name
			collision_shape.position = position
			collision_shape.rotation = rotation
	return ind

func handle_collision_settings(ind: int) -> int:
	var default_physics_type := args[ind]
	var num_of_default_collision_layers := int(args[ind + 1])
	ind += 2
	var default_layer := 0
	for i in num_of_default_collision_layers:
		default_layer |= 1 << int(args[ind])
		ind += 1
	var num_of_default_collision_masks := int(args[ind])
	ind += 1
	var default_mask := 0
	for i in num_of_default_collision_masks:
		default_mask |= 1 << int(args[ind])
		ind += 1
	var num_of_default_groups := int(args[ind])
	ind += 1
	var default_groups: Array[String] = []
	for i in num_of_default_groups:
		default_groups.append(args[ind])
		ind += 1
	
	# apply default settings to the root node
	var default_node_class_name: String
	var default_node_class := Node3D
	match default_physics_type:
		"STATIC_BODY":
			default_node_class_name = "StaticBody3D"
			default_node_class = StaticBody3D
		"CHARACTER_BODY":
			default_node_class_name = "CharacterBody3D"
			default_node_class = CharacterBody3D
		"RIGID_BODY":
			default_node_class_name = "RigidBody3D"
			default_node_class = RigidBody3D
		"ANIMATABLE_BODY":
			default_node_class_name = "AnimatableBody3D"
			default_node_class = AnimatableBody3D
		"AREA":
			default_node_class_name = "Area3D"
			default_node_class = Area3D
		"NODE":
			default_node_class_name = "Node3D"
			default_node_class = Node3D
		_:
			log_msg("Unknown collision type found: " + default_physics_type, "WARNING")
			default_node_class_name = "StaticBody3D"
			default_node_class = StaticBody3D
	if scene.get_class() != default_node_class_name:
		var old_scene := scene
		var new_scene := default_node_class.new()
		scene.replace_by(new_scene)
		scene = new_scene
		scene.name = old_scene.name
		old_scene.free()
	if default_node_class_name != "Node3D":
		scene.collision_layer = default_layer
		scene.collision_mask = default_mask
	for group in default_groups:
		scene.add_to_group(group, true)
	
	var number_of_settings := int(args[ind])
	ind += 1
	for i in number_of_settings:
		var node_name := args[ind].validate_node_name()
		var node_type_str := args[ind + 1]
		var layer_override_count := args[ind + 2]
		ind += 3
		var layer_override := 0
		if layer_override_count == "null":
			layer_override = default_layer
		else:
			for j in int(layer_override_count):
				layer_override |= 1 << int(args[ind])
				ind += 1
		
		var mask_override_count := args[ind]
		ind += 1
		var mask_override := 0
		if mask_override_count == "null":
			mask_override = default_mask
		else:
			for j in int(mask_override_count):
				mask_override |= 1 << int(args[ind])
				ind += 1
		
		var group_override_count := args[ind]
		ind += 1
		var group_overrides: Array[String] = []
		if group_override_count == "null":
			group_overrides = default_groups
		else:
			for j in int(group_override_count):
				group_overrides.append(args[ind])
				ind += 1
		
		var node_class_name: String
		var node_class := Node3D
		match node_type_str:
			"STATIC_BODY":
				node_class_name = "StaticBody3D"
				node_class = StaticBody3D
			"CHARACTER_BODY":
				node_class_name = "CharacterBody3D"
				node_class = CharacterBody3D
			"RIGID_BODY":
				node_class_name = "RigidBody3D"
				node_class = RigidBody3D
			"ANIMATABLE_BODY":
				node_class_name = "AnimatableBody3D"
				node_class = AnimatableBody3D
			"AREA":
				node_class_name = "Area3D"
				node_class = Area3D
			"NODE":
				node_class_name = "Node3D"
				node_class = Node3D
			_:
				log_msg("Unknown collision type found: " + node_type_str, "WARNING")
				node_class_name = "StaticBody3D"
				node_class = StaticBody3D
		
		var parent: Node3D
		if node_name == "Collisions":
			# then the root node is meant
			if scene.get_class() != node_class_name:
				var old_scene := scene
				var new_scene := node_class.new()
				scene.replace_by(new_scene)
				scene = new_scene
				scene.name = old_scene.name
				old_scene.free()
				if node_class_name != "Node3D":
					scene.collision_layer = layer_override
					scene.collision_mask = mask_override
				for group in group_overrides:
					scene.add_to_group(group, true)
			parent = scene
		else:
			var new_node := node_class.new()
			scene.add_child(new_node)
			new_node.owner = scene
			new_node.name = node_name
			if node_class_name != "Node3D":
				new_node.collision_layer = layer_override
				new_node.collision_mask = mask_override
			for group in group_overrides:
				new_node.add_to_group(group, true)
			parent = new_node
		
		var number_of_objs := int(args[ind])
		ind += 1
		for j in number_of_objs:
			var child_name := args[ind].validate_node_name()
			if child_name.ends_with("-convcolonly"):
				child_name = child_name.substr(0, child_name.length() - 12)
			ind += 1
			var node := find_node(scene, child_name)
			node.owner = null
			node.reparent(parent, false)
			node.owner = scene
		
	return ind

func rgb_channel_to_flag(rgb: String) -> BaseMaterial3D.TextureChannel:
	match rgb:
		"red":
			return BaseMaterial3D.TextureChannel.TEXTURE_CHANNEL_RED
		"green":
			return BaseMaterial3D.TextureChannel.TEXTURE_CHANNEL_GREEN
		"blue":
			return BaseMaterial3D.TextureChannel.TEXTURE_CHANNEL_BLUE
		"all":
			return BaseMaterial3D.TextureChannel.TEXTURE_CHANNEL_GRAYSCALE
		"alpha":
			return BaseMaterial3D.TextureChannel.TEXTURE_CHANNEL_ALPHA
		_:
			return BaseMaterial3D.TextureChannel.TEXTURE_CHANNEL_GRAYSCALE

func find_node(root: Node, s: String, max_depth := -1, current_depth := 0) -> Node3D:
	if max_depth != -1 and current_depth > max_depth:
		return null
	if root.name == s:
		return root
	for child in root.get_children():
		var found := find_node(child, s, max_depth, current_depth + 1)
		if (found != null):
			return found
	return null

func get_texture_by_name(material: BaseMaterial3D, name: String) -> Texture2D:
	match name:
		"texture_albedo":
			return material.get_texture(BaseMaterial3D.TEXTURE_ALBEDO)
		"texture_metallic":
			return material.get_texture(BaseMaterial3D.TEXTURE_METALLIC)
		"texture_roughness":
			return material.get_texture(BaseMaterial3D.TEXTURE_ROUGHNESS)
		"texture_emission":
			return material.get_texture(BaseMaterial3D.TEXTURE_EMISSION)
		"texture_normal":
			return material.get_texture(BaseMaterial3D.TEXTURE_NORMAL)
		_:
			log_msg("UNSUPPORTED TEXTURE FOUND: " + name, "ERROR")
			return Texture2D.new()

func insert_after_line(source: String, line: String, content: String) -> String:
	var lines := source.split("\n")
	for i in lines.size():
		if lines[i].strip_edges() == line.strip_edges():
			lines.insert(i + 1, content)
			break
	return "\n".join(lines)

func insert_before_line(source: String, line: String, content: String) -> String:
	var lines := source.split("\n")
	for i in lines.size():
		if lines[i].strip_edges() == line.strip_edges():
			lines.insert(i, content)
			break
	return "\n".join(lines)

func change_line(source: String, line: String, new_line: String) -> String:
	var lines := source.split("\n")
	for i in lines.size():
		if lines[i].strip_edges() == line.strip_edges():
			lines[i] = new_line
			break
	return "\n".join(lines)

func remove_line(source: String, line: String) -> String:
	var lines := source.split("\n")
	for i in lines.size():
		if lines[i].strip_edges() == line.strip_edges():
			lines.remove_at(i)
			break
	return "\n".join(lines)

func find_line_by_start(source: String, line_start: String) -> String:
	var lines := source.split("\n")
	for i in lines.size():
		if lines[i].strip_edges().begins_with(line_start.strip_edges()):
			return lines[i].strip_edges()
	return ""

func get_line_number(source: String, line: String) -> int:
	var lines := source.split("\n")
	for i in lines.size():
		if lines[i].strip_edges() == line.strip_edges():
			return i
	return -1

func free_node_and_children(node: Node) -> void:
	for child in node.get_children():
		free_node_and_children(child)
	node.free()
	
func convert_to_rounded_float_str(f: float, precision := 1_000_000) -> String:
	var rounded := roundi(f * precision)
	var s := str(rounded)
	if s.length() < 7:
		s = "0." + "0".repeat(6 - s.length()) + s
	else:
		s = s.substr(0, s.length() - 6) + "." + s.substr(s.length() - 6)
	s += "000000000" # make sure the string is at least 9 characters long
	return s.substr(0, 9)

func handle_animation_player(root: Node, animations_path: String, animation_libraries_path: String, lib_name: String) -> AnimationPlayer:
	var children := root.get_children()
	var anim_player: AnimationPlayer = null
	for child in children:
		if child is AnimationPlayer:
			var list: PackedStringArray = child.get_animation_list()
			var library := AnimationLibrary.new()
			for name in list:
				var anim: Animation = child.get_animation(name)
				if not DirAccess.dir_exists_absolute(animations_path):
					DirAccess.make_dir_recursive_absolute(animations_path)
				for i in anim.get_track_count():
					anim.track_set_imported(i, false)
				ResourceSaver.save(anim, animations_path + name + ".res", ResourceSaver.FLAG_CHANGE_PATH)
				anim = load(animations_path + name + ".res")
				library.add_animation(name, anim)
			if not DirAccess.dir_exists_absolute(animation_libraries_path):
				DirAccess.make_dir_recursive_absolute(animation_libraries_path)
			ResourceSaver.save(library, animation_libraries_path + lib_name + ".res", ResourceSaver.FLAG_CHANGE_PATH)
			library = load(animation_libraries_path + lib_name + ".res")
			anim_player = AnimationPlayer.new()
			anim_player.add_animation_library(lib_name, library)
			scene.remove_child(child)
			free_node_and_children(child)
			scene.add_child(anim_player)
			anim_player.owner = scene
			anim_player.name = "AnimationPlayer"
			break
	# we only support one animation player per scene! it doesn't really make sense for there to be multiple,
	# and it would mess with library names
	if anim_player != null:
		return anim_player
	for child in children:
		anim_player = handle_animation_player(child, animations_path, animation_libraries_path, lib_name)
		if anim_player != null:
			return anim_player
	return null

class MeshInstanceAndSurfaceIndex:
	var mesh_instance: MeshInstance3D
	var surface_idx: int


func handle_material_animations(ind: int, anim_player: AnimationPlayer, lib_name: String, blender_to_actual_mat_name: Dictionary):
	var action_count := int(args[ind])
	ind += 1
	for i in action_count:
		var action_name := args[ind]
		if action_name.ends_with("-loop"):
			action_name = action_name.substr(0, action_name.length() - "-loop".length())
		elif action_name.ends_with("loop"):
			action_name = action_name.substr(0, action_name.length() - "loop".length())
		var autoplay := true if args[ind + 1] == "true" else false
		var loop := true if args[ind + 2] == "true" else false
		ind += 3
		var anim: Animation = load(paths["animation_save_path"] + action_name + ".res")
		if autoplay:
			anim_player.autoplay = lib_name + "/" + action_name
		if loop:
			anim.loop_mode = Animation.LOOP_LINEAR
		else:
			anim.loop_mode = Animation.LOOP_NONE
	var count := int(args[ind])
	ind += 1
	for i in count:
		var fcurves := int(args[ind])
		ind += 1
		var rgb := ["r", "g", "b"]
		for j in fcurves:
			var idx := int(args[ind])
			var prop = ""
			if idx == 0:
				# base color
				prop = "albedo_color:" + rgb[j]
			elif idx == 1:
				# metallic
				prop = "metallic"
			elif idx == 2:
				# roughness
				prop = "roughness"
			elif idx == 4:
				prop = "albedo_color:a"
			var action_name := args[ind + 1]
			if action_name.ends_with("-loop"):
				action_name = action_name.substr(0, action_name.length() - "-loop".length())
			elif action_name.ends_with("loop"):
				action_name = action_name.substr(0, action_name.length() - "loop".length())
			var mat_name: String = blender_to_actual_mat_name[args[ind + 2]]
			var mat: Material = load(paths["material_save_path"] + mat_name + ".tres")
			var anim: Animation = load(paths["animation_save_path"] + action_name + ".res")
			# find all mesh instances that use the material
			var arr: Array[MeshInstanceAndSurfaceIndex] = []
			get_mesh_instances_using_material(scene, mat, arr)
			var track_arr := PackedInt64Array()
			track_arr.resize(arr.size())
			for k in arr.size():
				var track_idx := anim.add_track(Animation.TYPE_VALUE)
				anim.track_set_path(track_idx, arr[k].mesh_instance.name + ":mesh:surface_" + str(arr[k].surface_idx) + "/material:" + prop)
				track_arr[k] = track_idx
			var keyframes := int(args[ind + 3])
			ind += 4
			for k in keyframes:
				var x := float(args[ind])
				var y := float(args[ind + 1])
				ind += 2
				for track_idx in track_arr:
					# we ALWAYS assume 30 fps animation!!
					anim.track_insert_key(track_idx, x / 30.0, y)
			if not DirAccess.dir_exists_absolute(paths["animation_save_path"]):
				DirAccess.make_dir_recursive_absolute(paths["animation_save_path"])
			ResourceSaver.save(anim, paths["animation_save_path"] + action_name + ".res", ResourceSaver.FLAG_CHANGE_PATH)
	return ind

func get_mesh_instances_using_material(root: Node, material: Material, array: Array[MeshInstanceAndSurfaceIndex]):
	if root is MeshInstance3D:
		for i in root.mesh.get_surface_count():
			if root.mesh.surface_get_material(i) == material:
				var miasi = MeshInstanceAndSurfaceIndex.new()
				miasi.mesh_instance = root
				miasi.surface_idx = i
				array.append(miasi)
	for child in root.get_children():
		get_mesh_instances_using_material(child, material, array)

func handle_shaders(ind: int, blender_to_actual_mat_name: Dictionary):
	var number_of_shaders := int(args[ind])
	ind += 1
	for i in number_of_shaders:
		var mat_name: String = blender_to_actual_mat_name[args[ind]]
		var shader_mat := ShaderMaterial.new()
		var shader := Shader.new()
		shader.code = args[ind + 1]
		var num_uniforms := int(args[ind + 2])
		ind += 3
		for j in num_uniforms:
			var var_name := args[ind]
			var value := args[ind + 1]
			# we are kind of assuming here that value will always be a resource
			# this is the case right now, but may change in the future
			shader_mat.set_shader_parameter(var_name, load(value))
			ind += 2
		if not DirAccess.dir_exists_absolute(paths["shader_save_path"]):
			DirAccess.make_dir_recursive_absolute(paths["shader_save_path"])
		ResourceSaver.save(shader, paths["shader_save_path"] + mat_name + ".gdshader", ResourceSaver.FLAG_CHANGE_PATH)
		shader = load(paths["shader_save_path"] + mat_name + ".gdshader")
		shader_mat.shader = shader
		if not DirAccess.dir_exists_absolute(paths["material_save_path"]):
			DirAccess.make_dir_recursive_absolute(paths["material_save_path"])
		var arr: Array[MeshInstanceAndSurfaceIndex] = []
		if ResourceLoader.exists(paths["material_save_path"] + mat_name + ".tres"):
			var prev_mat := load(paths["material_save_path"] + mat_name + ".tres")
			get_mesh_instances_using_material(scene, prev_mat, arr)
			DirAccess.remove_absolute(paths["material_save_path"] + mat_name + ".tres")
		ResourceSaver.save(shader_mat, paths["material_save_path"] + mat_name + "Shader.tres", ResourceSaver.FLAG_CHANGE_PATH)
		shader_mat = load(paths["material_save_path"] + mat_name + "Shader.tres")
		if arr.size() > 0:
			for el in arr:
				el.mesh_instance.mesh.surface_set_material(el.surface_idx, shader_mat)
		
	return ind

func handle_light_settings(ind: int):
	var number_of_objects := int(args[ind])
	ind += 1
	for i in number_of_objects:
		var obj_name := args[ind].validate_node_name()
		var light := find_node(scene, obj_name)
		var settings_count := int(args[ind + 1])
		ind += 2
		for j in settings_count:
			var key := args[ind]
			var val_count := int(args[ind + 1])
			var can_add := ((light is OmniLight3D and not key.begins_with("spot_"))
				or (light is SpotLight3D and not key.begins_with("omni_"))
				or (light is DirectionalLight3D and not key.begins_with("spot_") and not key.begins_with("omni_")))
			if val_count == 1:
				if can_add:
					var value := args[ind + 2]
					if key == "light_cull_mask":
						# special case
						var lower20bits := int(value)
						var top12bits: int = ~((1 << 20) - 1) & light.light_cull_mask
						var new_mask := lower20bits | top12bits
						light[key] = new_mask
					elif value == "false":
						light[key] = false # would not get converted to false otherwise
					else:
						light[key] = type_convert(value, typeof(light[key]))
				ind += 3
			else:
				ind += 2
				for k in val_count:
					if can_add:
						var value := args[ind]
						if value == "false":
							light[key] = false # would not get converted to false otherwise
						else:
							light[key][k] = type_convert(value, typeof(light[key][k]))
					ind += 1
	return ind

func instantiate_child_scenes(ind: int):
	var number_of_instances := int(args[ind])
	ind += 1
	var scene_info_file := FileAccess.open("res://.tmp.goblend", FileAccess.READ)
	if scene_info_file == null:
		log_msg("temporary file for scene paths not found! (.tmp.goblend)", "ERROR")
	for i in number_of_instances:
		scene_info_file.seek(0)
		var blender_scene_path := args[ind]
		var scene_name := args[ind + 1].validate_node_name()
		var node_for_transform := find_node(scene, scene_name, 1)
		var position := node_for_transform.position
		var rotation := node_for_transform.rotation
		var scale := node_for_transform.scale
		scene.remove_child(node_for_transform)
		free_node_and_children(node_for_transform)
		ind += 2
		# find scene
		var scene_path := ""
		log_msg("Looking for child scene: " + blender_scene_path)
		while scene_info_file.get_position() < scene_info_file.get_length():
			var line := scene_info_file.get_line()
			if line.begins_with(blender_scene_path):
				scene_path = scene_info_file.get_line().strip_edges()
				break
		var packed_scene: PackedScene = load(scene_path + ".tscn")
		var scene_root: Node3D = packed_scene.instantiate()
		scene.add_child(scene_root)
		scene_root.owner = scene
		if scene_name.ends_with("__tmp_name"):
			scene_name = scene_name.substr(0, scene_name.find("__tmp_name"))
		scene_root.name = scene_name
		scene_root.position = position
		scene_root.rotation = rotation
		scene_root.scale = scale
	
	var predefined_scenes_count := int(args[ind])
	ind += 1
	for i in predefined_scenes_count:
		var obj_name := args[ind].validate_node_name()
		var scene_path := args[ind + 1]
		log_msg("Replacing " + obj_name + " with scene at " + scene_path)
		ind += 2
		var obj_node := find_node(scene, obj_name)
		var position := obj_node.position
		var rotation := obj_node.rotation
		var scale := obj_node.scale
		scene.remove_child(obj_node)
		free_node_and_children(obj_node)
		
		var packed_scene: PackedScene = load(scene_path)
		var scene_root: Node3D = packed_scene.instantiate()
		scene.add_child(scene_root)
		scene_root.owner = scene
		scene_root.name = obj_name
		scene_root.position = position
		scene_root.rotation = rotation
		scene_root.scale = scale
	
	return ind
