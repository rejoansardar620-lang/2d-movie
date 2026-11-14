extends Node2D
class_name FamilyActor
## Reusable open-source 2D skeleton. Art layers come from the original
## Everyday_English_Project action rig, with family-specific heads and clothes.

var role_id: String = "mom"
var skeleton: Skeleton2D
var bones: Dictionary = {}
var mouth: Polygon2D
var adult_scale: float = 0.40
var face_right: bool = true
var stage_x: float = 0.0


func add_bone(parent: Node2D, name_id: String, offset: Vector2, bone_length: float) -> Bone2D:
	var bone := Bone2D.new()
	bone.name = name_id
	bone.position = offset
	bone.set_autocalculate_length_and_angle(false)
	bone.length = bone_length
	# Bone2D's default rest transform is a zero matrix. An invertible
	# rest pose is mandatory, otherwise Skeleton2D emits det == 0 errors.
	bone.rest = bone.transform
	parent.add_child(bone)
	bones[name_id] = bone
	return bone


func attach_paint(parent: Node2D, filename: String, pivot: Vector2, depth: int = 0) -> void:
	var sprite := Sprite2D.new()
	sprite.name = filename + "_art"
	sprite.centered = false
	sprite.position = -pivot
	sprite.z_index = depth
	sprite.texture = load("res://godot_movie/assets/characters/%s/%s.png" % [role_id, filename])
	parent.add_child(sprite)


func configure(id: String) -> void:
	role_id = id
	adult_scale = 0.40 if id == "dad" or id == "mom" else 0.29
	skeleton = Skeleton2D.new()
	skeleton.name = "Skeleton2D"
	# Assemble the complete hierarchy before attaching it to the live tree:
	# Bone2D otherwise tries to calculate rest data on every incomplete joint.
	var hip := add_bone(skeleton, "hip", Vector2.ZERO, 60)
	for side in ["far", "near"]:
		var x := -35.0 if side == "far" else 36.0
		var thigh := add_bone(hip, side + "_thigh", Vector2(x, 70), 200)
		attach_paint(thigh, "thigh", Vector2(44, 15), -3 if side == "far" else 0)
		var shin := add_bone(thigh, side + "_shin", Vector2(0, 200), 195)
		attach_paint(shin, "shin", Vector2(38, 14), -3 if side == "far" else 0)
		var foot := add_bone(shin, side + "_foot", Vector2(0, 195), 75)
		attach_paint(foot, "foot", Vector2(34, 40), -2 if side == "far" else 1)
	attach_paint(hip, "pelvis", Vector2(95, 8), 0)
	var spine := add_bone(hip, "spine", Vector2(0, -2), 208)
	attach_paint(spine, "torso", Vector2(100, 225), 1)
	for side in ["far", "near"]:
		var x := 52.0 if side == "far" else -55.0
		var arm := add_bone(spine, side + "_arm", Vector2(x, -183), 143)
		attach_paint(arm, "upper_arm", Vector2(37, 12), -2 if side == "far" else 3)
		var forearm := add_bone(arm, side + "_forearm", Vector2(0, 143), 138)
		attach_paint(forearm, "forearm", Vector2(25, 10), -2 if side == "far" else 3)
		var hand := add_bone(forearm, side + "_hand", Vector2(0, 138), 70)
		attach_paint(hand, "hand", Vector2(16, 8), -2 if side == "far" else 4)
	var head := add_bone(spine, "head", Vector2(14, -206), 100)
	attach_paint(head, "head", Vector2(112, 212), 5)
	mouth = Polygon2D.new()
	mouth.name = "VisemeMouth"
	mouth.position = Vector2(51, -68)
	mouth.color = Color("#7a3536")
	mouth.z_index = 7
	head.add_child(mouth)
	set_viseme("X")
	skeleton.scale = Vector2(adult_scale, adult_scale)
	add_child(skeleton)


func set_stage(x: float, floor_y: float) -> void:
	stage_x = x
	position = Vector2(x, floor_y - 465.0 * adult_scale)


func set_viseme(symbol: String) -> void:
	if mouth == null:
		return
	var rx := 11.0
	var ry := 6.0
	match symbol:
		"X", "A":
			mouth.visible = false
			return
		"B", "G":
			rx = 10.0
			ry = 3.0
		"F", "H":
			rx = 6.0
			ry = 10.0
		_:
			rx = 15.0
			ry = 10.0
	var points := PackedVector2Array()
	for i in range(16):
		var angle := TAU * float(i) / 16.0
		points.append(Vector2(rx * cos(angle), ry * sin(angle)))
	mouth.polygon = points
	mouth.visible = true


func apply_action(seconds: float, action: String, look_right: bool, symbol: String) -> void:
	face_right = look_right
	skeleton.scale.x = adult_scale if look_right else -adult_scale
	set_viseme(symbol)
	var theta := seconds * 9.0
	var breathing := sin(seconds * 2.0) * 0.013
	bones["spine"].rotation = breathing
	bones["head"].rotation = sin(seconds * 1.8) * 0.035
	for side in ["near", "far"]:
		bones[side + "_thigh"].rotation = 0.0
		bones[side + "_shin"].rotation = 0.0
		bones[side + "_arm"].rotation = 0.05
		bones[side + "_forearm"].rotation = -0.1
	if action == "walk":
		for side in ["near", "far"]:
			var phase := theta + (PI if side == "far" else 0.0)
			bones[side + "_thigh"].rotation = 0.42 * sin(phase)
			bones[side + "_shin"].rotation = 0.26 * max(0.0, -sin(phase))
			bones[side + "_arm"].rotation = -0.32 * sin(phase)
		position.y += sin(theta * 2.0) * 0.25
	elif action == "talk" or action == "point":
		bones["near_arm"].rotation = -1.1 if action == "point" else -0.58
		bones["near_forearm"].rotation = -0.48 if action == "point" else -0.25
		bones["head"].rotation += 0.04 * sin(seconds * 4.0)
	elif action == "wave":
		bones["near_arm"].rotation = -2.1 + sin(seconds * 6.0) * 0.13
		bones["near_forearm"].rotation = -0.5
	elif action == "laugh":
		bones["near_arm"].rotation = -1.45
		bones["near_forearm"].rotation = -0.6
		bones["head"].rotation = -0.15 + 0.07 * sin(seconds * 5.0)
	elif action == "sit":
		for side in ["near", "far"]:
			bones[side + "_thigh"].rotation = -1.2
			bones[side + "_shin"].rotation = 1.1
	elif action == "listen":
		bones["head"].rotation = 0.10 + 0.035 * sin(seconds * 2.0)
