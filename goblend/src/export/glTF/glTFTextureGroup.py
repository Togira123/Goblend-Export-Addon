import bpy


class MaterialName(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()


class glTFTextureGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    # the materials that are to be replaced by this texture group
    materials: bpy.props.CollectionProperty(type=MaterialName)
