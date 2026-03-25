import bpy


class StringValue(bpy.types.PropertyGroup):
    value: bpy.props.StringProperty()


class IntValue(bpy.types.PropertyGroup):
    value: bpy.props.IntProperty()


class glTFPhysicsBody(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    type: bpy.props.StringProperty()

    layers: bpy.props.CollectionProperty(type=IntValue)
    masks: bpy.props.CollectionProperty(type=IntValue)
    groups: bpy.props.CollectionProperty(type=StringValue)
