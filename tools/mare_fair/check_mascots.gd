extends SceneTree
## Headless check for the Mare Fair mascots: identities, catalogue, prompts, schedules,
## and the one-time population migration. No world is loaded.
const NOTES := preload("res://world/characters/mare_fair/placeholders.gd")
const BALLOON := preload("res://world/characters/mare_fair/balloon.gd")
var failures := 0
var checks := 0


func _initialize() -> void:
	run.call_deferred()


func check(ok: bool, label: String) -> void:
	checks += 1
	print("MARE_FAIR ", "PASS " if ok else "FAIL ", label)
	if not ok:
		failures += 1


func run() -> void:
	var identity_script: Script = load("res://world/characters/hybrid_mare/pony_identity.gd")
	var races := {
		"fair_flyer": identity_script.Race.PEGASUS,
		"soiree": identity_script.Race.EARTH,
		"matinee": identity_script.Race.PEGASUS,
		"morning_mimosa": identity_script.Race.EARTH,
		"fun_raiser": identity_script.Race.UNICORN,
	}
	var catalog: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/characters/background/catalog.json"))
	var config_script: Script = load("res://world/population/pony_population_config.gd")
	var config: RefCounted = config_script.new()
	config.defaults()
	for id: String in NOTES.IDS:
		var identity: Resource = load("res://world/characters/background/%s.tres" % id)
		check(identity != null and str(identity.get("id")) == id, id + " identity")
		if identity == null: continue
		check(int(identity.get("race")) == int(races[id]), id + " race")
		check(identity.get("cutie_mark") != null, id + " mark")
		check(str(identity.get("hair_scene")).begins_with("res://world/characters/background/"), id + " borrowed hair")
		check(catalog.get(id, "") == "res://world/characters/background/%s.tscn" % id, id + " catalog")
		check(config.assignments.get(id, "") == "ponyville", id + " fresh assignment")
		check(FileAccess.file_exists(str(identity.get("ai_profile"))), id + " profile")
		var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(str(identity.get("ai_profile"))))
		check(FileAccess.file_exists(str(profile.get("prompt", ""))), id + " prompt")
		var schedule_path := "res://world/ai/schedules/%s.json" % id
		check(FileAccess.file_exists(schedule_path), id + " schedule")
		var schedule: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(schedule_path))
		check(str(schedule.get("default_location", "")) == BALLOON.SPOT_ID, id + " balloon schedule")
		check(NOTES.NOTES.has(id) and str(NOTES.NOTES[id]).length() > 40, id + " placeholder note")
	check(config.HOUSEHOLDS.members("soiree") == ["matinee", "soiree"], "twins share a home")
	var saved: Dictionary = config.as_dict()
	for id: String in NOTES.IDS:
		saved.assignments.erase(id)
	saved.erase("mare_fair_added")
	var migrated: RefCounted = config_script.new()
	check(migrated.apply_data(saved), "old save accepts missing flag")
	var all_back := true
	for id: String in NOTES.IDS:
		if migrated.assignments.get(id, "") != "ponyville": all_back = false
	check(all_back and migrated.mare_fair_added, "old save gains the five")
	var edited: Dictionary = migrated.as_dict()
	edited.assignments.erase("fun_raiser")
	var kept: RefCounted = config_script.new()
	check(kept.apply_data(edited), "later roster edit loads")
	check(not kept.assignments.has("fun_raiser"), "a removed mascot stays removed")
	check(BALLOON.SPOT_ID == "mare_fair_balloon", "balloon hangout")
	print("MARE_FAIR_DONE checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
