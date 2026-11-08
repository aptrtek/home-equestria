extends Node
## Parks the Mare Fair balloon once a world is up, and adds the five mascots to an
## existing save the first time. A fresh world already has them from the merged roster.

const BALLOON := preload("res://mods/mare_fair/balloon.gd")
const PONY := "res://world/characters/background/background_pony.gd"
const GLASSES := "res://world/characters/background/accessories/vinyl_glasses.scn"
const IDS: Array[String] = ["fair_flyer", "soiree", "matinee", "morning_mimosa", "fun_raiser"]
const GLASSED: Array[String] = ["fun_raiser", "morning_mimosa"]
var _dressed: Dictionary = {}


func _ready() -> void:
	Mods.on_node(PONY, _dress)
	Mods.world_ready.connect(_on_world)
	if is_instance_valid(Mods.game): _on_world(Mods.game)


func _process(_delta: float) -> void:
	for pony: Variant in _dressed.keys():
		if not is_instance_valid(pony):
			_dressed.erase(pony)
			continue
		if pony.get("_model") != _dressed[pony]: _dress(pony)


func _dress(pony: Node) -> void:
	var who: Resource = pony.get("identity")
	if who == null or not who.has_method("character"): return
	var id := str(who.call("character"))
	if id not in IDS: return
	var model: Variant = pony.get("_model")
	if id in GLASSED: _glasses(pony)
	_dressed[pony] = model


func _glasses(pony: Node) -> void:
	var skeleton: Variant = pony.get("hair_skeleton")
	if not skeleton is Skeleton3D or not ResourceLoader.exists(GLASSES): return
	if (skeleton as Skeleton3D).get_node_or_null("MareFairGlassesAttachment") != null: return
	var who: Resource = pony.get("identity")
	who = who.duplicate()
	pony.set("identity", who)
	var accessories: Array = who.get("accessories")
	if "MareFairGlasses" not in accessories: accessories.append("MareFairGlasses")
	var attachment := BoneAttachment3D.new()
	attachment.name = "MareFairGlassesAttachment"
	attachment.bone_name = "mHead"
	(skeleton as Skeleton3D).add_child(attachment)
	var source: Node = load(GLASSES).instantiate()
	attachment.add_child(source)
	var meshes: Array[Node] = source.find_children("*", "MeshInstance3D", true, false)
	if source is MeshInstance3D: meshes.append(source)
	for mesh: MeshInstance3D in meshes:
		mesh.reparent(attachment, false)
		mesh.name = "MareFairGlasses"
	if source.get_parent() == attachment and not source is MeshInstance3D: source.queue_free()


func _on_world(game: Node) -> void:
	if not is_instance_valid(game): return
	_park(game)
	_enroll(game)


func _park(game: Node) -> void:
	var town := game.get_node_or_null("Zones/PonyvilleTown")
	if town == null: return
	BALLOON.attach(town)


func _enroll(game: Node) -> void:
	var population: Node = game.get("population")
	if population == null: return
	var config: Object = population.get("config")
	if config == null or not config.has_method("assign"): return
	var state: Dictionary = Mods.state("mare_fair")
	if bool(state.get("enrolled", false)): return
	var assignments: Dictionary = config.get("assignments")
	var changed := false
	for id: String in IDS:
		if not assignments.has(id):
			config.assign(id, "ponyville")
			changed = true
	if changed and config.has_method("save_file"):
		config.save_file(str(population.get("config_path")))
	state["enrolled"] = true
	Mods.save_changed()
