import bpy


def is_not_action_picked_already(self, action):
    if action.library != None:
        return False
    scene = bpy.context.scene
    for item in scene.animation_panel_props:
        if item.animation == action:
            return False
    return True


class AnimationPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    animation: bpy.props.PointerProperty(name="Animation", type=bpy.types.Action, poll=is_not_action_picked_already)
    autoplay: bpy.props.BoolProperty(
        name="Autoplay", description="Mark Animation to play automatically on load", default=False
    )
    loop: bpy.props.BoolProperty(name="Loop", description="Make the animation loop", default=False)
