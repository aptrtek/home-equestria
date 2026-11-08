extends RefCounted
## Recolor a borrowed background mane and tail. Same trick as Anon's hair
## (player_pony.gd): texture brightness picks between two colours. Materials are
## duplicated so the donor pony is left alone.

const PALETTE := {
	"fair_flyer": [Color("c4a15a"), Color("f4e2a4")],
	"soiree": [Color("5bb8d0"), Color("a6e4f2")],
	"matinee": [Color("6ec4dc"), Color("c4eef8")],
	"morning_mimosa": [Color("187a34"), Color("22b14c")],
	"fun_raiser": [Color("e07a18"), Color("ffc07a")],
}


static func apply(pony: Node, model: Node) -> void:
	if pony == null or model == null: return
	var identity: Resource = pony.get("identity")
	if identity == null or not identity.has_method("character"): return
	var id := str(identity.call("character"))
	if not PALETTE.has(id): return
	var pair: Array = PALETTE[id]
	var dark: Color = pair[0]
	var light: Color = pair[1]
	var meshes: Array = [model] if model is MeshInstance3D else model.find_children("*", "MeshInstance3D", true, false)
	for mesh: MeshInstance3D in meshes:
		var name_lower := str(mesh.name).to_lower()
		if mesh.mesh == null or not (name_lower.contains("mane") or name_lower.contains("tail")): continue
		for surface in mesh.mesh.get_surface_count():
			var active := mesh.get_active_material(surface) as ShaderMaterial
			if active == null: continue
			var material := active.duplicate() as ShaderMaterial
			var current: Variant = material.get_shader_parameter("color")
			var alpha := 1.0
			if current is Color: alpha = (current as Color).a
			if material.get_shader_parameter("base_texture") != null:
				material.set_shader_parameter("replace_texture_palette", true)
				material.set_shader_parameter("texture_palette_source_a", Color.BLACK)
				material.set_shader_parameter("texture_palette_source_b", Color.WHITE)
				material.set_shader_parameter("texture_palette_a", dark)
				material.set_shader_parameter("texture_palette_b", light)
				material.set_shader_parameter("color", Color(1.0, 1.0, 1.0, alpha))
			else:
				material.set_shader_parameter("replace_texture_palette", false)
				material.set_shader_parameter("color", Color(light.r, light.g, light.b, alpha))
			var shadow: Variant = material.get_shader_parameter("shadow_color")
			if shadow is Color and (shadow as Color).a > 0.0 and pony.has_method("_shade_of"):
				material.set_shader_parameter("shadow_color", pony.call("_shade_of", light))
			var ink := material.next_pass as ShaderMaterial
			if ink != null:
				ink = ink.duplicate() as ShaderMaterial
				var line: Color = identity.get("mane_line")
				if ink.shader != null and str(ink.shader.resource_path).ends_with("outline-tinted.gdshader"):
					ink.set_shader_parameter("outline_color", line)
				else:
					ink.set_shader_parameter("color", line)
					if pony.has_method("_shade_of"):
						ink.set_shader_parameter("shadow_color", pony.call("_shade_of", line))
				material.next_pass = ink
			mesh.set_surface_override_material(surface, material)
