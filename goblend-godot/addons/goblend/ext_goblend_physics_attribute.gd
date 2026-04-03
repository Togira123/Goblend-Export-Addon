@tool
class_name GLTFDocumentExtensionEXTGoblendPhysicsAttribute extends GLTFDocumentExtension

var ext_name := "EXT_goblend_physics_body_attribute"

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

func _import_node(_state: GLTFState, gltf_node: GLTFNode, _json: Dictionary, node: Node) -> Error:
	var ext = gltf_node.get_additional_data(ext_name)
	if ext == null:
		if node is CollisionObject3D:
			if gltf_node.get_additional_data("EXT_goblend_godot_scene"):
				# this node is the root of a scene instance, do not change any layers etc
				return OK
			# if it's not present it means that there are no layers, masks or groups set
			node.collision_layer = 0
			node.collision_mask = 0
		return OK
	if node is CollisionObject3D:
		# the layers are given as an int array
		var sum := 0
		if ext.has("layers"):
			for layer in ext["layers"]:
				sum += 2 ** layer
		node.collision_layer = sum
		sum = 0
		if ext.has("masks"):
			for mask in ext["masks"]:
				sum += 2 ** mask
		node.collision_mask = sum
		if ext.has("groups"):
			for group in ext["groups"]:
				node.add_to_group(group, true)
	else:
		return ERR_INVALID_DATA

	return OK
