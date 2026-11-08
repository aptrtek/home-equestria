extends "res://world/population/pony_population.gd"
## The Mare Fair mascots live at their balloon, so they take no house in Ponyville and
## nopony who was already there has to share. At bedtime a pony with no house settles
## where she is.

const BALLOON_DWELLERS: Array[String] = ["fair_flyer", "soiree", "matinee", "morning_mimosa", "fun_raiser"]


func _assign_houses() -> void:
	super()
	var removed := false
	for id: String in BALLOON_DWELLERS:
		if houses.has(id):
			houses.erase(id)
			removed = true
	if not removed: return
	_houses_version += 1
	for house: Node3D in get_tree().get_nodes_in_group("house_interiors"):
		if house.has_method("set_sleepers"): house.set_sleepers(residents_of(house.place_id()))
	preload("res://world/save_file.gd").write(config_path.get_base_dir().path_join("homes.json"), houses)
