extends Node3D
## Parked Mare Fair balloon on Balloon Hill, where the five mascots gather.
## Twilight's balloon stays the flyable one. This one does not lift: no helm, no burner.
## Shape and colours follow the 2025 desktop art: red and light-blue vertical gores,
## a red basket, and a light-blue star. The top of that picture is cropped, so the
## crown is only a plain rounded close of the same stripes. The picture is not shipped.

const FITTINGS := preload("res://world/vehicles/balloon/basket.gd")
const ENVELOPE_SHADER := preload("res://mods/mare_fair/envelope.gdshader")
const RED := Color(0.941176, 0.282353, 0.313725)
const STRIPE_BLUE := Color(0.376471, 0.564706, 0.815686)
const STAR_BLUE := Color(0.490196, 0.705882, 0.878431)
const MODEL := "res://world/props/rnl/rnl_ponyville_airballoon/prefab.scn"
const ENVELOPE_SURFACES: Array[int] = [2, 3]
const BASKET_SURFACES: Array[int] = [1, 6, 7, 8, 10]
const STAR_SURFACES: Array[int] = [0, 5]
const SPOT_ID := "mare_fair_balloon"
## Clear of Twilight's balloon (280.5, -296), the easel (266, -285.5) and the picnic tables.
const POSE := Vector3(262.0, 6.78, -308.0)
## Door faces back toward Twilight's balloon and the hill path.
const YAW := -2.15
var _body: StaticBody3D
var _meet: Marker3D
var _grounded := false
var _spotted := false
var _tries := 0


static func attach(town: Node) -> void:
	if not town is Node3D or town.get_node_or_null("MareFairBalloon") != null: return
	var node := (load("res://mods/mare_fair/balloon.gd") as Script).new() as Node3D
	node.name = "MareFairBalloon"
	town.add_child(node)
	node.global_position = POSE
	node.rotation.y = YAW


func _ready() -> void:
	add_to_group("ai_observable")
	set_meta("ai_id", SPOT_ID)
	set_meta("ai_label", "Mare Fair balloon")
	_envelope()
	_basket()
	_meet = Marker3D.new()
	_meet.name = "Meet"
	_meet.position = Vector3(0, 0, -3.4)
	add_child(_meet)
	set_process(true)


func _process(_delta: float) -> void:
	_tries += 1
	if not _grounded: _snap_to_ground()
	_register_spot()
	if _spotted and (_grounded or _tries > 240): set_process(false)
	elif _tries > 480: set_process(false)


## The game's own town balloon model, repainted: striped envelope, red basket.
func _envelope() -> void:
	if not ResourceLoader.exists(MODEL): return
	var model: Node = load(MODEL).instantiate()
	add_child(model)
	var stripes := ShaderMaterial.new()
	stripes.shader = ENVELOPE_SHADER
	var red := FITTINGS.material(RED)
	var star := FITTINGS.material(STAR_BLUE)
	var meshes: Array[Node] = model.find_children("*", "MeshInstance3D", true, false)
	if model is MeshInstance3D: meshes.append(model)
	for mesh: MeshInstance3D in meshes:
		for surface in mesh.mesh.get_surface_count():
			if surface in ENVELOPE_SURFACES: mesh.set_surface_override_material(surface, stripes)
			elif surface in BASKET_SURFACES: mesh.set_surface_override_material(surface, red)
			elif surface in STAR_SURFACES: mesh.set_surface_override_material(surface, star)


## A solid block where the basket stands. It stays parked, so nopony boards it.
func _basket() -> void:
	_body = StaticBody3D.new()
	_body.name = "Basket"
	_body.collision_layer = 1
	_body.collision_mask = 0
	add_child(_body)
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(3.3, 1.7, 3.3)
	shape.shape = box
	shape.position.y = 0.8
	_body.add_child(shape)


func _snap_to_ground() -> void:
	if not is_inside_tree(): return
	var world := get_world_3d()
	if world == null: return
	var exclude: Array[RID] = []
	for body in find_children("*", "CollisionObject3D", true, false):
		exclude.append((body as CollisionObject3D).get_rid())
	if _body != null: exclude.append(_body.get_rid())
	var from := global_position + Vector3.UP * 40.0
	var query := PhysicsRayQueryParameters3D.create(from, global_position + Vector3.DOWN * 80.0, 1, exclude)
	var hit := world.direct_space_state.intersect_ray(query)
	if hit.is_empty(): return
	global_position.y = hit.position.y
	_grounded = true


func _on_navigation_ready() -> void:
	_spotted = false
	_register_spot()


func _register_spot() -> void:
	if not is_inside_tree() or _meet == null: return
	for service in get_tree().get_nodes_in_group("pony_navigation"):
		var content := service.get_parent() as Node3D
		if content == null or not content.is_ancestor_of(self): continue
		var layers: Variant = service.get("layers")
		if layers == null: continue
		if service.has_signal("navigation_ready") and not service.navigation_ready.is_connected(_on_navigation_ready):
			service.navigation_ready.connect(_on_navigation_ready)
		var local: Vector3 = content.to_local(_meet.global_position)
		var was_dirty: bool = bool(layers.get("dirty"))
		layers.call("add_hot_spot", SPOT_ID, Vector2(local.x, local.z), "social", 6.0, 6)
		if not was_dirty: layers.set("dirty", false)
		_spotted = true
