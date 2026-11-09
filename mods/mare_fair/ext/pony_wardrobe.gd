extends "res://world/characters/accessories/pony_wardrobe.gd"
## Fair Flyer's sun hat and Morning Mimosa's and Fun Raiser's glasses are worn by default and can
## be taken off and put back on through the game's own wardrobe. What is off is saved with the world.

const MARE_FAIR_WEAR := {
	"fair_flyer": "mare-fair-sun-hat",
	"morning_mimosa": "mare-fair-spiral-glasses",
	"fun_raiser": "mare-fair-half-moon-glasses",
}
const MARE_FAIR_MODELS := {
	"mare-fair-sun-hat": "res://mods/mare_fair/accessories/sun_hat.glb",
	"mare-fair-spiral-glasses": "res://mods/mare_fair/accessories/spiral_glasses.glb",
	"mare-fair-half-moon-glasses": "res://mods/mare_fair/accessories/half_moon_glasses.glb",
}
const MARE_FAIR_NAMES := {
	"mare-fair-sun-hat": "her sun hat",
	"mare-fair-spiral-glasses": "her glasses",
	"mare-fair-half-moon-glasses": "her glasses",
}


func wanted(id: String, season: String) -> Dictionary:
	var result: Dictionary = super(id, season)
	if not MARE_FAIR_WEAR.has(id): return result
	var kind: String = MARE_FAIR_WEAR[id]
	if kind in taken_off().get(id, []): return result
	# Her own hat wins over a seasonal or gifted one.
	if kind == "mare-fair-sun-hat":
		for other: Variant in HEADWEAR: result.erase(other)
	result[kind] = 0
	return result


func set_worn(id: String, spoken: String, on: bool) -> String:
	if not MARE_FAIR_WEAR.has(id): return super(id, spoken, on)
	var kind: String = MARE_FAIR_WEAR[id]
	var word := spoken.to_lower()
	var means: bool = word.contains("hat") if kind == "mare-fair-sun-hat" else (word.contains("glasses") or word.contains("spectacles") or word.contains("specs"))
	if not means: return super(id, spoken, on)
	var off: Array = taken_off().get(id, [])
	if on == (kind in off):
		if on: off.erase(kind)
		else: off.append(kind)
		if off.is_empty(): taken_off().erase(id)
		else: taken_off()[id] = off
		if game.world_context.has_method("_changed"): game.world_context._changed()
	return MARE_FAIR_NAMES[kind]


func _attach(pony: Node3D, kind: String, colour: Color) -> void:
	if not MARE_FAIR_MODELS.has(kind):
		super(pony, kind, colour)
		return
	var skeleton: Variant = pony.get("hair_skeleton")
	if not skeleton is Skeleton3D or not ResourceLoader.exists(MARE_FAIR_MODELS[kind]): return
	var bone: int = (skeleton as Skeleton3D).find_bone("mHead")
	if bone < 0: return
	var attachment := BoneAttachment3D.new()
	attachment.name = "Wear_" + kind
	attachment.bone_name = "mHead"
	(skeleton as Skeleton3D).add_child(attachment)
	var piece: Node3D = load(MARE_FAIR_MODELS[kind]).instantiate()
	attachment.add_child(piece)
	# The model is in the rig's rest space, so cancel the head's rest pose.
	piece.transform = (skeleton as Skeleton3D).get_bone_global_rest(bone).affine_inverse()
	_outline(piece)


func _outline(piece: Node) -> void:
	var line := ShaderMaterial.new()
	line.shader = preload("res://mods/mare_fair/accessories/outline.gdshader")
	var meshes: Array[Node] = piece.find_children("*", "MeshInstance3D", true, false)
	if piece is MeshInstance3D: meshes.append(piece)
	for mesh: MeshInstance3D in meshes:
		for surface in mesh.mesh.get_surface_count():
			var material: Material = mesh.mesh.surface_get_material(surface).duplicate()
			material.next_pass = line
			mesh.set_surface_override_material(surface, material)
