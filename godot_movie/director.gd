extends Node2D
## Reusable no-plugin dialogue director: room transitions, cinematic camera,
## four skeletal actors, lip shapes, reactions and character eye-lines.

const ROOMS := [
	"drawing_room", "drawing_room", "drawing_room",
	"kitchen", "kitchen", "kitchen",
	"balcony", "balcony", "balcony",
	"outside", "outside", "outside"
]
const FLOWERS := ["", "rose", "sunflower", "tulip", "daisy", "lily",
	"marigold", "lotus", "hibiscus", "orchid", "jasmine", ""]
const ROLES := ["dad", "mom", "boy", "girl"]
const TARGETS := [
	{"dad":240,"mom":976,"boy":574,"girl":752},
	{"dad":320,"mom":960,"boy":600,"girl":771},
	{"dad":274,"mom":995,"boy":626,"girl":809},
	{"dad":230,"mom":985,"boy":606,"girl":800},
	{"dad":272,"mom":958,"boy":615,"girl":784},
	{"dad":240,"mom":870,"boy":528,"girl":1035},
	{"dad":245,"mom":945,"boy":573,"girl":770},
	{"dad":245,"mom":970,"boy":575,"girl":768},
	{"dad":258,"mom":952,"boy":580,"girl":792},
	{"dad":270,"mom":1000,"boy":596,"girl":789},
	{"dad":235,"mom":1000,"boy":565,"girl":786},
	{"dad":230,"mom":1000,"boy":575,"girl":800}
]

var dialogue: Array = []
var rhubarb: Array = []
var people: Dictionary = {}
var stage: Sprite2D
var flower: Sprite2D
var camera: Camera2D
var music: AudioStreamPlayer
var captions: Label
var header: Label
var film_seconds: float = 0.0
var previous_room: String = ""


func json_file(path: String) -> Variant:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Required film metadata missing: " + path)
		return []
	return JSON.parse_string(file.get_as_text())


func _ready() -> void:
	dialogue = json_file("res://episode3/timings.json")
	var data: Variant = json_file("res://episode3/audio/rhubarb_cues.json")
	rhubarb = data.get("mouthCues", []) if data is Dictionary else []
	stage = Sprite2D.new()
	stage.name = "PaintedBackground"
	stage.position = Vector2(640, 360)
	add_child(stage)
	flower = Sprite2D.new()
	flower.name = "FlowerProp"
	flower.position = Vector2(1090, 475)
	flower.scale = Vector2(0.85, 0.85)
	add_child(flower)
	for role in ROLES:
		var actor := FamilyActor.new()
		actor.name = role.capitalize()
		add_child(actor)
		actor.configure(role)
		people[role] = actor
	camera = Camera2D.new()
	camera.position = Vector2(640, 360)
	add_child(camera)
	camera.make_current()
	var ui := CanvasLayer.new()
	ui.name = "Subtitles"
	add_child(ui)
	var plate := ColorRect.new()
	plate.position = Vector2(22, 643)
	plate.size = Vector2(1236, 56)
	plate.color = Color(0.08, 0.075, 0.065, 0.76)
	ui.add_child(plate)
	captions = Label.new()
	captions.position = Vector2(37, 648)
	captions.size = Vector2(1206, 48)
	captions.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	captions.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	captions.add_theme_font_size_override("font_size", 26)
	captions.add_theme_color_override("font_color", Color("#fff7e8"))
	ui.add_child(captions)
	header = Label.new()
	header.position = Vector2(38, 36)
	header.add_theme_font_size_override("font_size", 23)
	header.add_theme_color_override("font_color", Color("#fff9e5"))
	ui.add_child(header)
	music = AudioStreamPlayer.new()
	music.name = "FourSpeakerDialogue"
	music.stream = load("res://episode3/audio/narration.wav")
	add_child(music)
	music.play()
	set_process(true)


func speaking_at(time: float) -> Dictionary:
	for line in dialogue:
		if time >= line["start"] and time <= line["end"]:
			return line
	return {}


func viseme_at(time: float) -> String:
	for cue in rhubarb:
		if time >= cue["start"] and time < cue["end"]:
			return cue["value"]
	return "X"


func _process(delta: float) -> void:
	film_seconds += delta
	if music.playing:
		film_seconds = music.get_playback_position()
	var scene: int = mini(11, int(floor(film_seconds / 10.0)))
	var local: float = fmod(film_seconds, 10.0)
	var room: String = ROOMS[scene]
	if room != previous_room:
		previous_room = room
		stage.texture = load("res://godot_movie/assets/backgrounds/%s.png" % room)
	var word: String = FLOWERS[scene]
	flower.visible = word != ""
	if word != "":
		flower.texture = load("res://godot_movie/assets/flowers/%s.png" % word)
	flower.position = Vector2(1090, 478 + sin(film_seconds * 2.0) * 3.0)
	var line: Dictionary = speaking_at(film_seconds)
	var speaker: String = line.get("speaker", "")
	captions.text = line.get("text", "")
	header.text = "%s  •  %s" % [room.replace("_", " ").to_upper(), word.to_upper()]
	for role in ROLES:
		var actor: FamilyActor = people[role]
		var x: float = TARGETS[scene][role]
		var action: String = "listen"
		if scene in [3, 6, 9] and local < 3.2:
			var factor: float = clampf((local - (0.4 if role == "mom" else 0.0)) / 2.8, 0.0, 1.0)
			x -= 560 * (1.0 - factor * factor * (3.0 - 2.0 * factor))
			action = "walk"
		elif role == speaker:
			action = "point" if (scene % 2 == 0 and local < 6.0) else "talk"
		if scene == 11 and local > 8.5:
			action = "wave"
		var other_x: float = TARGETS[scene][speaker] if speaker != "" else 640.0
		if role == speaker:
			other_x = 640.0 if x > 640 else 960.0
		actor.set_stage(x, 632.0)
		actor.apply_action(film_seconds, action, other_x > x,
			viseme_at(film_seconds) if role == speaker else "X")
	var target_x: float = TARGETS[scene][speaker] if speaker != "" else 640.0
	var zoom: float = 1.00 if scene in [0, 3, 6, 9, 11] else 1.25
	camera.zoom = camera.zoom.lerp(Vector2(zoom, zoom), minf(1.0, delta * 3.0))
	camera.position = camera.position.lerp(Vector2(640 + (target_x - 640) * 0.27, 360), minf(1.0, delta * 2.7))
	if film_seconds >= 120.0:
		film_seconds = 0.0
		music.play()
