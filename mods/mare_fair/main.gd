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
## Script extensions do not work in the packaged game, so nothing here extends a game script.
## The mares wear the game's own hat and glasses items, which gives them the wardrobe, saving and
## the AI's take_off and put_on, and their own models are drawn in place of those items.
const WEAR := {
	"fair_flyer": ["cowpony-hat", "res://mods/mare_fair/accessories/sun_hat.glb"],
	"morning_mimosa": ["aviators", "res://mods/mare_fair/accessories/spiral_glasses.glb"],
	"fun_raiser": ["cat-eye-glasses", "res://mods/mare_fair/accessories/half_moon_glasses.glb"],
}
const OUTLINE := "res://mods/mare_fair/accessories/outline.gdshader"
const OWN_WEAR := "MareFairWear"
var _poll := 0.0
var _sister_check := 0.0
var _dressed: Dictionary = {}


func _ready() -> void:
	add_child(preload("res://mods/mare_fair/hand_wear.gd").new())
	Mods.on_node(PONY, _dress)
	Mods.world_ready.connect(_on_world)
	if is_instance_valid(Mods.game): _on_world(Mods.game)


func _process(delta: float) -> void:
	_poll -= delta
	if _poll <= 0.0:
		_poll = 1.0
		_keep_out_of_houses()
		_sync_wear()
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
	_give_wear(game)


## The mares live at their balloon. The game hands every resident a house, so theirs are taken back.
func _keep_out_of_houses() -> void:
	var game: Node = Mods.game
	if not is_instance_valid(game): return
	var population: Variant = game.get("population")
	if not is_instance_valid(population): return
	var houses: Variant = population.get("houses")
	if not houses is Dictionary: return
	var removed := false
	for id: String in IDS:
		if (houses as Dictionary).erase(id): removed = true
	if not removed: return
	population.set("_houses_version", int(population.get("_houses_version")) + 1)
	for house: Node in get_tree().get_nodes_in_group("house_interiors"):
		if house.has_method("set_sleepers"): house.call("set_sleepers", population.call("residents_of", house.call("place_id")))
	preload("res://world/save_file.gd").write(str(population.get("config_path")).get_base_dir().path_join("homes.json"), houses)


## Once per world: the mares own their hat and glasses, as the game's gifts.
func _give_wear(game: Node) -> void:
	var state: Dictionary = Mods.state("mare_fair")
	_separate_glasses(game, state)
	if bool(state.get("wear_given", false)): return
	var wardrobe: Variant = game.get("wardrobe")
	if not is_instance_valid(wardrobe) or game.get("world_context") == null or game.world_context._read_only: return
	var gifts: Dictionary = wardrobe.call("gifts")
	for id: String in WEAR:
		var item := "wear:%s:0" % str(WEAR[id][0])
		var list: Array = gifts.get(id, [])
		if item not in list:
			list.append(item)
			gifts[id] = list
	state["wear_given"] = true
	Mods.save_changed()


## Morning Mimosa's stand-in changed, so each mare's piece can be told apart when it is carried.
func _separate_glasses(game: Node, state: Dictionary) -> void:
	if bool(state.get("glasses_separated", false)): return
	var wardrobe: Variant = game.get("wardrobe")
	if not is_instance_valid(wardrobe) or game.get("world_context") == null or game.world_context._read_only: return
	var gifts: Dictionary = wardrobe.call("gifts")
	var list: Array = gifts.get("morning_mimosa", [])
	if "wear:cat-eye-glasses:0" in list:
		list.erase("wear:cat-eye-glasses:0")
		list.append("wear:aviators:0")
		gifts["morning_mimosa"] = list
	var off: Dictionary = wardrobe.call("taken_off")
	var taken: Array = off.get("morning_mimosa", [])
	if "cat-eye-glasses" in taken:
		taken.erase("cat-eye-glasses")
		taken.append("aviators")
		off["morning_mimosa"] = taken
	state["glasses_separated"] = true


## Draws each mare's own model while the game has its stand-in item on her.
func _sync_wear() -> void:
	var game: Node = Mods.game
	if not is_instance_valid(game): return
	var mares: Variant = game.get("mares")
	if not mares is Array: return
	for pony: Variant in mares:
		if not is_instance_valid(pony): continue
		var who: Variant = pony.get("identity")
		if who == null or not WEAR.has(str(who.get("id"))): continue
		var skeleton: Variant = pony.get("hair_skeleton")
		if not skeleton is Skeleton3D: continue
		var row: Array = WEAR[str(who.get("id"))]
		var stand_in: Node3D
		for node: Node in (pony as Node).find_children("Wear_" + str(row[0]), "", true, false):
			if not node.is_queued_for_deletion(): stand_in = node as Node3D
		var own := (skeleton as Node).get_node_or_null(OWN_WEAR)
		if stand_in == null:
			if own != null: own.queue_free()
			continue
		stand_in.visible = false
		if own == null: _attach_wear(skeleton, str(row[1]))


func _attach_wear(skeleton: Skeleton3D, path: String) -> void:
	var bone := skeleton.find_bone("mHead")
	if bone < 0 or not ResourceLoader.exists(path): return
	var attachment := BoneAttachment3D.new()
	attachment.name = OWN_WEAR
	attachment.bone_name = "mHead"
	skeleton.add_child(attachment)
	var piece: Node3D = load(path).instantiate()
	attachment.add_child(piece)
	piece.transform = skeleton.get_bone_global_rest(bone).affine_inverse()
	var line := ShaderMaterial.new()
	line.shader = load(OUTLINE)
	var meshes: Array[Node] = piece.find_children("*", "MeshInstance3D", true, false)
	if piece is MeshInstance3D: meshes.append(piece)
	for mesh: MeshInstance3D in meshes:
		for surface in mesh.mesh.get_surface_count():
			# Only the frame of the spiral glasses is outlined; the lens and spiral stay clean.
			if surface > 0 and path.ends_with("spiral_glasses.glb"): continue
			var material: Material = mesh.mesh.surface_get_material(surface).duplicate()
			material.next_pass = line
			mesh.set_surface_override_material(surface, material)


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
