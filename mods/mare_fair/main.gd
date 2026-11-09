extends Node
## Parks the Mare Fair balloon once a world is up, and adds the five mascots to an
## existing save the first time. A fresh world already has them from the merged roster.

const BALLOON := preload("res://mods/mare_fair/balloon.gd")
const PONY := "res://world/characters/background/background_pony.gd"
const GLASSES := "res://world/characters/background/accessories/vinyl_glasses.scn"
const IDS: Array[String] = ["fair_flyer", "soiree", "matinee", "morning_mimosa", "fun_raiser"]
## Morning Mimosa's and Fun Raiser's own glasses are part of their hair files, so nopony
## needs a borrowed pair.
const GLASSED: Array[String] = []
## The player named here starts a new world already married to Soirée. To earn her hoof instead,
## put {"start_married_to_soiree": false} in user://mods/data/mare_fair/settings.json.
const HUSBAND := "aperture_tech"
const WIFE := "soiree"
const AI_CONFIG := preload("res://world/ai/ai_config.gd")
const SISTER := "matinee"
const SISTER_KNOWS := "\n\nSoirée and aperture_tech are married. Matinée is thrilled about it, has opinions on the wedding outfits, and will set anypony straight who gets ideas about her sister."
var _sister_check := 0.0
var _dressed: Dictionary = {}


func _ready() -> void:
	Mods.on_node(PONY, _dress)
	Mods.world_ready.connect(_on_world)
	if is_instance_valid(Mods.game): _on_world(Mods.game)


func _process(delta: float) -> void:
	_sister_check -= delta
	if _sister_check <= 0.0:
		_sister_check = 2.0
		_tell_sister()
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
	_start_marriage(game)


## Matinée knows about the marriage only while it is true in the game, however it came about.
func _tell_sister() -> void:
	var game: Node = Mods.game
	if not is_instance_valid(game): return
	var director: Variant = game.get("director")
	var runtime: Variant = game.get("relationship_runtime")
	if not is_instance_valid(director) or not is_instance_valid(runtime): return
	var characters: Variant = director.get("characters")
	if not characters is Dictionary or not (characters as Dictionary).has(SISTER): return
	var row: Dictionary = characters[SISTER]
	var prompt := str(row.get("prompt", ""))
	var married: bool = str(runtime.get("bonds").record_for(WIFE).stage) == "married"
	if married and not prompt.contains(SISTER_KNOWS): row["prompt"] = prompt + SISTER_KNOWS
	elif not married and prompt.contains(SISTER_KNOWS): row["prompt"] = prompt.replace(SISTER_KNOWS, "")


## Once per world, and never over a relationship that has already got somewhere.
func _start_marriage(game: Node) -> void:
	var state: Dictionary = Mods.state("mare_fair")
	if bool(state.get("marriage_settled", false)): return
	var runtime: Variant = game.get("relationship_runtime")
	if not is_instance_valid(runtime): return
	var bonds: Node = runtime.get("bonds")
	if bonds == null or bonds.get("context") == null or bonds.context._read_only: return
	state["marriage_settled"] = true
	Mods.save_changed()
	if not _starts_married(): return
	if str(bonds.record_for(WIFE).stage) != "acquaintance": return
	var record: Dictionary = bonds.record_for(WIFE)
	record.stage = "married"
	record.familiarity = 100.0
	record.trust = 100.0
	record.dating_since = bonds.day()
	record.engaged_since = bonds.day()
	bonds._save(WIFE, record)
	bonds.mark_met(WIFE)
	bonds.mark_name_known(WIFE)


func _starts_married() -> bool:
	if str(AI_CONFIG.load_config().get_value("player_name", "")).strip_edges() != HUSBAND: return false
	var path := Mods.data_folder("mare_fair").path_join("settings.json")
	var settings: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
	return bool(settings.get("start_married_to_soiree", true)) if settings is Dictionary else true


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
