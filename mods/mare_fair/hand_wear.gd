extends Node
## Taking Fair Flyer's hat or Morning Mimosa's or Fun Raiser's glasses off by hand. It goes into
## your hand as the real thing. Desktop: look at it and press Y. VR: free hand at her head, pull
## the trigger. Do the same holding it to put it back, or hand it to her as any gift.
## Taken without asking it is up to her: a friend may laugh, anypony else will mind. A pony who
## trusts you can have it taken off while she sleeps; one who doesn't wakes up cross and keeps it.

const PIECES := {
	"fair_flyer": {"word": "hat", "kind": "cowpony-hat", "name": "sun hat", "rise": 0.26, "model": "res://mods/mare_fair/accessories/sun_hat.glb"},
	"morning_mimosa": {"word": "glasses", "kind": "aviators", "name": "glasses", "rise": 0.12, "model": "res://mods/mare_fair/accessories/spiral_glasses.glb"},
	"fun_raiser": {"word": "glasses", "kind": "cat-eye-glasses", "name": "glasses", "rise": 0.1, "model": "res://mods/mare_fair/accessories/half_moon_glasses.glb"},
}
const DESKTOP_REACH := 2.2
const AIM_WIDTH := 0.22
const HAND_REACH := 0.3
const TRIGGER_ON := 0.7
const TRIGGER_OFF := 0.3
const SIDES: Array[String] = ["left", "right"]
const SWAPPED := "mare_fair_swapped"
var _pulled := {"left": false, "right": false}
var _swap_check := 0.0


func _ready() -> void:
	add_to_group("interaction_hint_sources")


func _input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_Y): return
	if not _desktop(): return
	var pony := _aimed()
	if pony == null: return
	var game: Node = Mods.game
	_use(pony, "desktop", (game.call("_find_camera", game.get("player")) as Camera3D).global_transform)
	get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_swap_check -= delta
	if _swap_check <= 0.0:
		_swap_check = 0.25
		_swap_held_models()
	if _desktop() or not is_instance_valid(Mods.game): return
	var inventory := _inventory()
	if inventory == null or Mods.game.get("xr_active") != true: return
	for side: String in SIDES:
		var sample: Dictionary = inventory.hand_sample(side)
		var trigger := float(sample.get("trigger", 0.0))
		if not _pulled[side] and trigger > TRIGGER_ON and bool(sample.get("active", false)):
			_pulled[side] = true
			var pony := _at_hand(sample.get("grip_position", Vector3.INF), side)
			if pony != null: _use(pony, side, sample.get("pose", Transform3D.IDENTITY))
		elif _pulled[side] and trigger < TRIGGER_OFF:
			_pulled[side] = false


func interaction_hint() -> Dictionary:
	if not _desktop(): return {}
	var pony := _aimed()
	if pony == null: return {}
	var piece: Dictionary = PIECES[_id(pony)]
	var back := _holds_hers(pony, "desktop") or _is_off(pony)
	return {"target": pony, "text": "Y · %s %s" % ["Put on" if back else "Take", piece.name], "point": _point(pony)}


func _desktop() -> bool:
	var game: Node = Mods.game
	return is_instance_valid(game) and game.get("xr_active") != true and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED


func _inventory() -> Node:
	return Mods.game.get("inventory") as Node if is_instance_valid(Mods.game) else null


func _wardrobe() -> Node:
	return Mods.game.get("wardrobe") as Node


func _id(pony: Node) -> String:
	var who: Variant = pony.get("identity")
	return str(who.get("id")) if who != null else ""


func _item_id(id: String) -> String:
	return "wear:%s:0" % str(PIECES[id].kind)


func _carried() -> Dictionary:
	var state: Dictionary = Mods.state("mare_fair")
	if not state.get("carried") is Dictionary: state["carried"] = {}
	return state.carried


func _ponies() -> Array:
	var found: Array = []
	var mares: Variant = Mods.game.get("mares") if is_instance_valid(Mods.game) else null
	if mares is Array:
		for pony: Variant in mares:
			if is_instance_valid(pony) and PIECES.has(_id(pony)) and not pony.is_held(): found.append(pony)
	return found


func _point(pony: Node) -> Vector3:
	var affection: Node = pony.get_node_or_null("Affection")
	if affection == null: return Vector3.INF
	return affection.mouth_point() + Vector3.UP * float(PIECES[_id(pony)].rise)


func _is_worn(pony: Node) -> bool:
	return _item_id(_id(pony)) in (_wardrobe().gifts().get(_id(pony), []) as Array) and not _is_off(pony)


func _is_off(pony: Node) -> bool:
	return str(PIECES[_id(pony)].kind) in (_wardrobe().taken_off().get(_id(pony), []) as Array)


func _holds_hers(pony: Node, side: String) -> bool:
	var inventory := _inventory()
	var item: Variant = inventory.held.get(side)
	return is_instance_valid(item) and str(item.get_meta("item_id", "")) == _item_id(_id(pony)) and str(_carried().get(_item_id(_id(pony)), "")) == _id(pony)


## Whether this hand can act on her: holding her piece, or free with something to take or restore.
func _can_use(pony: Node, side: String) -> bool:
	if _holds_hers(pony, side): return true
	return not _inventory().hand_busy(side) and (_is_worn(pony) or _is_off(pony))


func _aimed() -> Node3D:
	var game: Node = Mods.game
	if _inventory() == null: return null
	var camera: Variant = game.call("_find_camera", game.get("player"))
	if not camera is Camera3D: return null
	var origin: Vector3 = (camera as Camera3D).global_position
	var forward: Vector3 = -(camera as Camera3D).global_basis.z
	for pony: Node3D in _ponies():
		var point := _point(pony)
		if not point.is_finite() or not _can_use(pony, "desktop"): continue
		var along := (point - origin).dot(forward)
		if along > 0.0 and along < DESKTOP_REACH and (origin + forward * along).distance_to(point) < AIM_WIDTH: return pony
	return null


func _at_hand(palm: Variant, side: String) -> Node3D:
	if not palm is Vector3 or not (palm as Vector3).is_finite(): return null
	for pony: Node3D in _ponies():
		var point := _point(pony)
		if point.is_finite() and point.distance_to(palm) < HAND_REACH and _can_use(pony, side): return pony
	return null


func _use(pony: Node3D, side: String, pose: Transform3D) -> void:
	var id := _id(pony)
	if _holds_hers(pony, side): _put_back(pony, id, side)
	elif _is_off(pony): _restore(pony, id)
	else: _take(pony, id, side, pose)


## Back on after she took it off herself through the wardrobe.
func _restore(pony: Node3D, id: String) -> void:
	var wardrobe := _wardrobe()
	var piece: Dictionary = PIECES[id]
	if str(wardrobe.set_worn(id, str(piece.word), true)).is_empty(): return
	wardrobe.dress(pony, id, wardrobe.call("_season"))
	_after_returned(pony, id, piece)


func _put_back(pony: Node3D, id: String, side: String) -> void:
	var inventory := _inventory()
	var item: RigidBody3D = inventory.held[side]
	var token := str(item.get_meta("token", ""))
	if not inventory.inventory.consume(token): return
	inventory.held.erase(side)
	inventory.loose.erase(token)
	inventory._track.erase(side)
	inventory._claim(side, false)
	item.queue_free()
	inventory._refresh_holding()
	inventory._haptic(side)
	var wardrobe := _wardrobe()
	var list: Array = wardrobe.gifts().get(id, [])
	var item_id := _item_id(id)
	if item_id not in list: list.append(item_id)
	wardrobe.gifts()[id] = list
	_carried().erase(item_id)
	Mods.save_changed()
	wardrobe.dress(pony, id, wardrobe.call("_season"))
	_after_returned(pony, id, PIECES[id])


func _after_returned(pony: Node3D, id: String, piece: Dictionary) -> void:
	if pony.get("sleeping") == true: _remember(id, "While you slept, Anon put your %s back on you." % piece.name)
	else: _tell(id, "Anon put your %s back on you." % piece.name)


func _take(pony: Node3D, id: String, side: String, pose: Transform3D) -> void:
	var piece: Dictionary = PIECES[id]
	var runtime: Variant = pony.get_meta("relationship_runtime", null)
	var bonds: Variant = runtime.get("bonds") if is_instance_valid(runtime) else null
	var friendly: bool = bonds == null or bonds.welcomes(id, "hug")
	var asleep: bool = pony.get("sleeping") == true
	if asleep and not friendly:
		_woken_cross(pony, id, piece, bonds)
		return
	if not _into_hand(id, side, pose): return
	var wardrobe := _wardrobe()
	var list: Array = wardrobe.gifts().get(id, [])
	list.erase(_item_id(id))
	wardrobe.gifts()[id] = list
	_carried()[_item_id(id)] = id
	Mods.save_changed()
	wardrobe.dress(pony, id, wardrobe.call("_season"))
	_swap_held_models()
	if asleep:
		_remember(id, "While you slept, Anon gently took off your %s and kept it safe." % piece.name)
		return
	var note := "" if piece.word == "hat" else " You cannot see well without them. Depending on the moment that may be funny or a real problem."
	if friendly:
		_tell(id, "Anon took your %s off you without asking and is holding it, playfully. Laugh or object, whichever suits you right now.%s" % [piece.name, note])
		return
	pony.set_dialogue_expression("annoyed")
	bonds.unwanted_contact(id, "hug")
	_tell(id, "Anon took your %s off you without asking and is holding it, and you did not welcome that.%s" % [piece.name, note])


## She doesn't trust you, and you were reaching for her things while she slept.
func _woken_cross(pony: Node3D, id: String, piece: Dictionary, bonds: Variant) -> void:
	var rest: Node = Mods.game.get_node_or_null("NightRest")
	if rest == null or not rest.has_method("wake_up") or not rest.wake_up(id): return
	pony.set_dialogue_expression("angry")
	if bonds != null: bonds.unwanted_contact(id, "hug")
	_tell(id, "You woke to find Anon reaching for your %s while you slept. You do not trust him enough for that, and you are a little angry." % piece.name)


func _into_hand(id: String, side: String, pose: Transform3D) -> bool:
	var inventory := _inventory()
	var item_id := _item_id(id)
	var store: Variant = inventory.inventory
	store.grant(item_id, 1)
	var slot := -1
	for index: int in (store.slots as Array).size():
		var row: Dictionary = store.slots[index]
		if not row.is_empty() and str(row.id) == item_id: slot = index
	if slot < 0: return false
	if inventory.take_slot(side, slot, pose, false): return true
	store.discard(item_id)
	return false


## In a hand or set down, a carried piece looks like the mare's own.
func _swap_held_models() -> void:
	var game: Node = Mods.game
	if not is_instance_valid(game) or _inventory() == null or game.get("wardrobe") == null: return
	var carried := _carried()
	for item_id: String in carried.keys():
		var owner_id := str(carried[item_id])
		if item_id in (_wardrobe().gifts().get(owner_id, []) as Array): carried.erase(item_id)
	if carried.is_empty(): return
	for item: Variant in _inventory().loose.values():
		if not is_instance_valid(item) or item.has_meta(SWAPPED): continue
		var item_id := str(item.get_meta("item_id", ""))
		if carried.has(item_id): _swap(item, str(PIECES[str(carried[item_id])].model))


func _swap(item: Node3D, path: String) -> void:
	if not ResourceLoader.exists(path): return
	for mesh: Node in item.find_children("*", "GeometryInstance3D", true, false): (mesh as GeometryInstance3D).visible = false
	var piece: Node3D = load(path).instantiate()
	item.add_child(piece)
	var meshes: Array[Node] = piece.find_children("*", "MeshInstance3D", true, false)
	if piece is MeshInstance3D: meshes.append(piece)
	if not meshes.is_empty(): piece.position = -(meshes[0] as MeshInstance3D).get_aabb().get_center()
	item.set_meta(SWAPPED, true)


func _remember(id: String, text: String) -> void:
	var context: Variant = Mods.game.get("world_context")
	if is_instance_valid(context): context.record("affection", text, [id])


func _tell(id: String, summary: String) -> void:
	var director: Variant = Mods.game.get("director")
	if is_instance_valid(director) and director.has_method("_on_physical_reaction"):
		director.call("_on_physical_reaction", "contact", id, false, summary)
