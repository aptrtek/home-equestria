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
const INTERIOR := Color(0.165, 0.188, 0.275)
const SEGMENTS := 48
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
	var profile := PackedVector2Array([
		Vector2(1.25, 0.0), Vector2(1.55, 0.4), Vector2(2.15, 1.15),
		Vector2(2.8, 2.2), Vector2(3.15, 3.45), Vector2(2.95, 4.55),
		Vector2(2.25, 5.4), Vector2(1.25, 6.05), Vector2(0.18, 6.4),
	])
	var mesh := MeshInstance3D.new()
	mesh.name = "Envelope"
	mesh.mesh = _lathe(profile)
	var material := ShaderMaterial.new()
	material.shader = ENVELOPE_SHADER
	mesh.material_override = material
	mesh.position.y = 1.42
	add_child(mesh)


func _lathe(profile: PackedVector2Array) -> ArrayMesh:
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var rings := profile.size()
	for ring in rings:
		var radius := profile[ring].x
		var y := profile[ring].y
		var v := float(ring) / float(rings - 1)
		var previous: Vector2 = profile[maxi(ring - 1, 0)]
		var next: Vector2 = profile[mini(ring + 1, rings - 1)]
		var tangent := next - previous
		var normal_2d := Vector2(tangent.y, -tangent.x).normalized()
		if normal_2d.x < 0.0: normal_2d = -normal_2d
		for seg in SEGMENTS + 1:
			var u := float(seg) / float(SEGMENTS)
			var ang := u * TAU
			var out := Vector3(cos(ang), 0.0, sin(ang))
			tool.set_uv(Vector2(u, v))
			tool.set_normal((out * normal_2d.x + Vector3.UP * normal_2d.y).normalized())
			tool.add_vertex(Vector3(out.x * radius, y, out.z * radius))
	var stride := SEGMENTS + 1
	for ring in rings - 1:
		for seg in SEGMENTS:
			var a := ring * stride + seg
			var b := a + 1
			var c := a + stride
			var d := c + 1
			tool.add_index(a)
			tool.add_index(c)
			tool.add_index(b)
			tool.add_index(b)
			tool.add_index(c)
			tool.add_index(d)
	return tool.commit()


func _basket() -> void:
	_body = StaticBody3D.new()
	_body.name = "Basket"
	_body.collision_layer = 1
	_body.collision_mask = 0
	add_child(_body)
	FITTINGS.box(_body, Vector3(0, 0.16, 0.1), Vector3(2.7, 0.16, 2.35), INTERIOR)
	var deck := CollisionShape3D.new()
	var deck_box := BoxShape3D.new()
	deck_box.size = Vector3(2.7, 0.18, 2.4)
	deck.shape = deck_box
	deck.position = Vector3(0, 0.16, 0.1)
	_body.add_child(deck)
	for x in [-1.35, 1.35]:
		FITTINGS.box(_body, Vector3(x, 0.78, 0.1), Vector3(0.16, 1.24, 2.55), RED, true)
	FITTINGS.box(_body, Vector3(0, 0.78, 1.28), Vector3(2.7, 1.24, 0.16), RED, true)
	for x in [-0.9, 0.9]:
		FITTINGS.box(_body, Vector3(x, 0.78, -1.08), Vector3(0.78, 1.24, 0.16), RED, true)
	var ramp := StaticBody3D.new()
	ramp.name = "Ramp"
	ramp.collision_layer = 1
	ramp.collision_mask = 0
	ramp.position = Vector3(0, 0.14, -1.7)
	ramp.rotation.x = -0.2
	_body.add_child(ramp)
	FITTINGS.box(ramp, Vector3.ZERO, Vector3(1.05, 0.08, 1.05), RED, true)
	_star(Vector3(-1.46, 0.78, 0.1), -PI * 0.5)
	_star(Vector3(1.46, 0.78, 0.1), PI * 0.5)


func _star(at: Vector3, yaw: float) -> void:
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var outer := 0.46
	var inner := 0.19
	tool.set_normal(Vector3.FORWARD)
	tool.add_vertex(Vector3.ZERO)
	for i in 10:
		var ang := -PI * 0.5 + float(i) * PI / 5.0
		var radius := outer if i % 2 == 0 else inner
		tool.set_normal(Vector3.FORWARD)
		tool.add_vertex(Vector3(cos(ang) * radius, sin(ang) * radius, 0.0))
	for i in 10:
		tool.add_index(0)
		tool.add_index(1 + i)
		tool.add_index(1 + (i + 1) % 10)
	var mesh := MeshInstance3D.new()
	mesh.mesh = tool.commit()
	mesh.material_override = FITTINGS.material(STAR_BLUE)
	mesh.position = at
	mesh.rotation.y = yaw
	_body.add_child(mesh)


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
