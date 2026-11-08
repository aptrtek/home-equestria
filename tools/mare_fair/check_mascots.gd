extends SceneTree
## Confirms the Mare Fair mascots live in the mod and not in the base game.
## With `-- --mod-src mare_fair`, also checks the merged roster sees them.
const IDS: Array[String] = ["fair_flyer", "soiree", "matinee", "morning_mimosa", "fun_raiser"]
var failures := 0
var checks := 0


func _initialize() -> void:
	run.call_deferred()


func check(ok: bool, label: String) -> void:
	checks += 1
	print("MARE_FAIR ", "PASS " if ok else "FAIL ", label)
	if not ok: failures += 1


func run() -> void:
	var manifest: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://mods/mare_fair/mod.json"))
	check(manifest is Dictionary and str(manifest.get("id", "")) == "mare_fair", "mod.json")
	var base_catalog := FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://world/characters/background/catalog.json"))
	var base_assign := FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://world/population/default_assignments.json"))
	for id: String in IDS:
		check(ResourceLoader.exists("res://mods/mare_fair/ponies/%s.tscn" % id), id + " scene")
		var identity: Resource = load("res://mods/mare_fair/ponies/%s.tres" % id)
		check(identity != null and str(identity.get("id")) == id, id + " identity")
		check(str(identity.get("hair_scene")).begins_with("res://world/characters/background/"), id + " borrowed hair")
		check(str(identity.get("cutie_mark")).contains("mods/mare_fair/marks/") or identity.get("cutie_mark") != null, id + " mark")
		check(FileAccess.file_exists("res://mods/mare_fair/merge/world/ai/schedules/%s.json" % id), id + " schedule")
		check(not base_catalog.contains('"%s"' % id), id + " stays out of the base catalog")
		check(not base_assign.contains('"%s"' % id), id + " stays out of the base roster")
	check(load("res://mods/mare_fair/balloon.gd") != null, "balloon script")
	check(load("res://mods/mare_fair/envelope.gdshader") != null, "envelope shader")
	check(load("res://mods/mare_fair/main.gd") != null, "entry script")
	var merged := "res://world/characters/background/catalog.json"
	var virtual_catalog := FileAccess.get_file_as_string(merged)
	var mod_src := "--mod-src" in OS.get_cmdline_user_args()
	if mod_src:
		for id: String in IDS:
			check(virtual_catalog.contains(id), id + " merged into the live catalog")
	print("MARE_FAIR_DONE checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
