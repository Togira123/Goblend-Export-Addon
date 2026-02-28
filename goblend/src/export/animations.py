import bpy

from ..log import log


def get_data_block_at(obj, path):
    while True:
        firstDot = path.find(".")
        firstBracket = path.find("[")
        if firstDot == -1 and firstBracket == -1:
            return obj
        if firstBracket == 0:
            closingBracket = path.find("]")
            if path[firstBracket + 1] == '"':
                obj = obj[path[firstBracket + 2 : closingBracket - 1]]
            else:
                # it's an integer
                obj = obj[int(path[firstBracket + 1 : closingBracket])]
            path = path[closingBracket + 1 :]
        elif firstDot < firstBracket and firstDot >= 0:
            obj = getattr(obj, path[:firstDot])
            path = path[firstDot + 1 :]
        else:
            obj = getattr(obj, path[:firstBracket])
            path = path[firstBracket:]


def handle_animations():
    arr = []
    slot_count = 0
    for action in bpy.data.actions:
        if action.library == None:
            for slot in action.slots:
                if slot.target_id_type == "NODETREE":
                    subarr = handle_nodetree_animations(action, slot)
                    if len(subarr) > 0:
                        slot_count += 1
                        arr.extend(subarr)

    return [str(slot_count)] + arr


def handle_nodetree_animations(action, slot):
    users = slot.users()
    if len(users) == 0:
        return []
    if len(users) > 1:
        log(
            "Animation slot '" + slot.name + "' has multiple users! Only the first one will be used in Godot",
            "WARNING",
        )
    user = users[0]
    cb = action.layers[0].strips[0].channelbag(slot)
    arr = []
    fc_count = 0
    for fcurve in cb.fcurves:
        # is something like 'nodes["Principled BSDF"].inputs[4].default_value'
        data_path = fcurve.data_path
        node = get_data_block_at(user, data_path[: data_path.find(".")])
        if node.type != "BSDF_PRINCIPLED":
            # we can only animate properties directly on the bsdf
            continue
        if not data_path.endswith(".default_value"):
            # we can only animate default value things
            continue
        if not ".inputs[" in data_path:
            # we can only animate the inputs for the BSDF
            continue
        inp = data_path.find(".inputs[")
        idx = data_path[inp + len(".inputs[") : data_path.find("]", inp)]
        # supported inputs:
        # input 0 = base color
        # input 1 = metallic
        # input 2 = roughness
        # input 4 = alpha
        if idx != "0" and idx != "1" and idx != "2" and idx != "4":
            continue
        fc_count += 1
        arr.append(idx)
        arr.append(action.name)
        found = False
        for m in bpy.data.materials:
            if m.node_tree == user:
                arr.append(m.name)
                found = True
                break
        if not found:
            raise Exception("Material belonging to animation not found")
        arr.append(str(len(fcurve.keyframe_points)))
        for kf in fcurve.keyframe_points:
            arr.append(str(kf.co.x))
            arr.append(str(kf.co.y))

    return [str(fc_count)] + arr
