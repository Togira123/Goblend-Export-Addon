@tool
class_name Goblend extends EditorPlugin

var ext_goblend_physics_attribute := GLTFDocumentExtensionEXTGoblendPhysicsAttribute.new()
var ext_goblend_material := GLTFDocumentExtensionEXTGoblendMaterial.new()
var ext_goblend_light := GLTFDocumentExtensionEXTGoblendLight.new()
var ext_goblend_godot_scene := GLTFDocumentExtensionEXTGoblendGodotScene.new()
var ext_goblend_animation := GLTFDocumentExtensionEXTGoblendAnimation.new()
var convert_importer_mesh := GLTFDocumentExtensionConvertImporterMesh.new()
var ext_goblend_general := GLTFDocumentExtensionEXTGoblendGeneral.new()

func _enter_tree():
	GLTFDocument.register_gltf_document_extension(ext_goblend_physics_attribute)
	GLTFDocument.register_gltf_document_extension(ext_goblend_material)
	GLTFDocument.register_gltf_document_extension(ext_goblend_light)
	GLTFDocument.register_gltf_document_extension(ext_goblend_godot_scene)
	GLTFDocument.register_gltf_document_extension(ext_goblend_animation)
	GLTFDocument.register_gltf_document_extension(convert_importer_mesh)
	GLTFDocument.register_gltf_document_extension(ext_goblend_general)


func _exit_tree():
	GLTFDocument.unregister_gltf_document_extension(ext_goblend_physics_attribute)
	GLTFDocument.unregister_gltf_document_extension(ext_goblend_material)
	GLTFDocument.unregister_gltf_document_extension(ext_goblend_light)
	GLTFDocument.unregister_gltf_document_extension(ext_goblend_godot_scene)
	GLTFDocument.unregister_gltf_document_extension(ext_goblend_animation)
	GLTFDocument.unregister_gltf_document_extension(convert_importer_mesh)
	GLTFDocument.unregister_gltf_document_extension(ext_goblend_general)

static func log_msg(message: String, type := "INFO"):
	var msg := type + ": " + str(message)
	var now := Time.get_time_dict_from_system()
	msg = ("[%02d:%02d:%02d] (GODOT) " % [now["hour"], now["minute"], now["second"]]) + msg
	var log_file := FileAccess.open("res://goblend.log", FileAccess.READ_WRITE)
	log_file.seek_end()
	log_file.store_string(msg + "\n")
	log_file.close()
	print(msg)
