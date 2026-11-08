extends Node3D
## Parked Mare Fair balloon on Balloon Hill, where the five mascots gather.
## Twilight's balloon stays the flyable one. This one does not lift: no helm, no burner.
## The envelope is the town balloon mesh when that scenery is loaded, recolored; the
## basket is built here. No official Mare Fair balloon art was on the mascot pages.

const FITTINGS := preload("res://world/vehicles/balloon/basket.gd")
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
	var node := (load("res://world/characters/mare_fair/balloon.gd") as Script).new() as Node3D
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


func _envelope() -> void:
	var town := get_parent()
	var source := town.find_child("airballoon_01", true, false) as Node3D if town != null else null
	if source == null:
		_plain_envelope()
		return
	var copy := source.duplicate() as Node3D
	copy.name = "Envelope"
	copy.set_meta("ai_id", "")
	copy.set_meta("ai_label", "")
	add_child(copy)
	copy.transform = Transform3D.IDENTITY
	for body in copy.find_children("*", "CollisionObject3D", true, false):
		var collision := body as CollisionObject3D
		collision.collision_layer = 0
		collision.collision_mask = 0
	var purple := Color("6b3a86")
	var meshes: Array = copy.find_children("*", "MeshInstance3D", true, false)
	if copy is MeshInstance3D: meshes.append(copy)
	for mesh: MeshInstance3D in meshes:
		if mesh.mesh == null: continue
		for surface in mesh.mesh.get_surface_count():
			var active := mesh.get_active_material(surface)
			if active == null: continue
			var material := active.duplicate()
			if material is StandardMaterial3D:
				var standard := material as StandardMaterial3D
				standard.albedo_color = standard.albedo_color.lerp(purple, 0.62)
			elif material is ShaderMaterial:
				var color: Variant = (material as ShaderMaterial).get_shader_parameter("color")
				if color is Color:
					(material as ShaderMaterial).set_shader_parameter("color", (color as Color).lerp(purple, 0.5))
			mesh.set_surface_override_material(surface, material)
	var band := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = 2.55
	torus.outer_radius = 3.15
	band.mesh = torus
	band.material_override = FITTINGS.material(Color("e2bb62"))
	band.position.y = 5.35
	add_child(band)


func _plain_envelope() -> void:
	var mesh := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 3.1
	sphere.height = 7.2
	mesh.mesh = sphere
	mesh.material_override = FITTINGS.material(Color("6b3a86"))
	mesh.position.y = 5.6
	add_child(mesh)


func _basket() -> void:
	var wood := Color("955d31")
	var purple := Color("a877ad")
	var gold := Color("e2bb62")
	_body = StaticBody3D.new()
	_body.name = "Basket"
	_body.collision_layer = 1
	_body.collision_mask = 0
	add_child(_body)
	for i in 12:
		FITTINGS.box(_body, Vector3(-1.375 + i * 0.25, 0.18, 0), Vector3(0.243, 0.16, 2.6), wood.lightened(0.04 * (i % 3)))
	var deck := CollisionShape3D.new()
	var deck_box := BoxShape3D.new()
	deck_box.size = Vector3(3.0, 0.18, 2.7)
	deck.shape = deck_box
	deck.position.y = 0.17
	_body.add_child(deck)
	for x in [-1.5, 1.5]:
		FITTINGS.box(_body, Vector3(x, 0.82, 0), Vector3(0.14, 1.28, 2.7), purple, true)
		FITTINGS.box(_body, Vector3(x, 1.46, 0), Vector3(0.21, 0.14, 2.86), gold)
	FITTINGS.box(_body, Vector3(0, 0.82, 1.35), Vector3(3.0, 1.28, 0.14), purple, true)
	FITTINGS.box(_body, Vector3(0, 1.46, 1.35), Vector3(3.2, 0.14, 0.21), gold)
	for x in [-1.03, 1.03]:
		FITTINGS.box(_body, Vector3(x, 0.82, -1.35), Vector3(0.95, 1.28, 0.14), purple, true)
		FITTINGS.box(_body, Vector3(x, 1.46, -1.35), Vector3(0.95, 0.14, 0.21), gold)
	FITTINGS.box(_body, Vector3(0, 0.55, 1.02), Vector3(2.5, 0.12, 0.48), Color("714633"), true)
	var ramp := StaticBody3D.new()
	ramp.name = "Ramp"
	ramp.collision_layer = 1
	ramp.collision_mask = 0
	ramp.position = Vector3(0, 0.17, -1.82)
	ramp.rotation.x = -0.18
	_body.add_child(ramp)
	FITTINGS.box(ramp, Vector3.ZERO, Vector3(1.05, 0.09, 1.1), wood, true)
	FITTINGS.label(_body, Vector3(-1.62, 0.9, 0), "MARE FAIR", PI * 0.5)


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
		var layers: MapLayers = service.get("layers")
		if layers == null: continue
		if service.has_signal("navigation_ready") and not service.navigation_ready.is_connected(_on_navigation_ready):
			service.navigation_ready.connect(_on_navigation_ready)
		var local: Vector3 = content.to_local(_meet.global_position)
		var was_dirty: bool = layers.dirty
		layers.add_hot_spot(SPOT_ID, Vector2(local.x, local.z), "social", 6.0, 6)
		if not was_dirty: layers.dirty = false
		_spotted = true
