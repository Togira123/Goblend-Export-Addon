@tool
class_name GLTFDocumentExtensionEXTGoblendGodotScene extends GLTFDocumentExtension

var ext_name := "EXT_goblend_godot_scene"

func _import_preflight(_state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP

func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([ext_name])

func _parse_node_extensions(state: GLTFState, gltf_node: GLTFNode, extensions: Dictionary) -> Error:
	if not extensions.has(ext_name):
		return OK
	var ext: Dictionary = extensions[ext_name]
	gltf_node.set_additional_data(ext_name, ext)
	return OK

func _generate_scene_node(state: GLTFState, gltf_node: GLTFNode, _scene_parent: Node) -> Node3D:
	var ext = gltf_node.get_additional_data(ext_name)
	if ext == null:
		return null
	if ext.has("scene_path"):
		var scene_path: String = ext["scene_path"]
		if not scene_path.ends_with(".tscn"):
			scene_path += ".tscn"
		var packed_scene: PackedScene = load(scene_path)
		Goblend.log_msg("Loaded packed scene from " + scene_path)
		var scene_root: Node3D = packed_scene.instantiate()
		var scene_name := gltf_node.original_name
		if scene_name.ends_with("__tmp_name"):
			scene_name = scene_name.substr(0, scene_name.find("__tmp_name"))
		# to effectively change the name we have to set it on the resource_name
		gltf_node.resource_name = scene_name
		scene_root.transform = gltf_node.xform
		# remove children because otherwise they'll be added as children of the instantiated root node
		for n in scene_root.get_children():
			scene_root.remove_child(n)
			n.queue_free()
		# update the data to reflect whether this is a scene instance
		gltf_node.set_additional_data(ext_name, true)
		return scene_root
	# update the data to reflect whether this is a scene instance
	gltf_node.set_additional_data(ext_name, false)
	return null
