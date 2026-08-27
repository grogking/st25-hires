class_name StPaths
extends RefCounted
## Resolve the owner's GOG TREKCD directory. Game files are never in this repo.

const DEFAULT_TREKCD := "G:/star trek/Star Trek 25th Anniversary/TREKCD"
const DEFAULT_TREKCD_ALT := "G:/Star Trek/Star Trek 25th Anniversary/TREKCD"


static func cmdline_game_dir() -> String:
	var args := OS.get_cmdline_user_args()
	for i in range(args.size()):
		var a := args[i]
		if a == "--game-dir" and i + 1 < args.size():
			return args[i + 1]
		if a.begins_with("--game-dir="):
			return a.substr("--game-dir=".length())
	return ""


static func _push_unique(out: PackedStringArray, seen: Dictionary, p: String) -> void:
	var n := p.strip_edges()
	if n.is_empty() or seen.has(n):
		return
	seen[n] = true
	out.append(n)


static func candidate_dirs() -> PackedStringArray:
	var out := PackedStringArray()
	var seen := {}
	_push_unique(out, seen, cmdline_game_dir())
	_push_unique(out, seen, OS.get_environment("ST25_GAME_DIR"))
	if ProjectSettings.has_setting("st25/game_dir"):
		_push_unique(out, seen, str(ProjectSettings.get_setting("st25/game_dir")))
	if FileAccess.file_exists("res://st25.cfg"):
		var txt := FileAccess.get_file_as_string("res://st25.cfg")
		for line in txt.split("\n"):
			var s := line.strip_edges()
			if s.begins_with("game_dir="):
				_push_unique(out, seen, s.substr("game_dir=".length()).strip_edges())
	_push_unique(out, seen, DEFAULT_TREKCD)
	_push_unique(out, seen, DEFAULT_TREKCD_ALT)
	_push_unique(out, seen, OS.get_executable_path().get_base_dir().path_join("TREKCD"))
	return out


static func _has_data_dir(path: String) -> bool:
	var da := DirAccess.open(path)
	if da == null:
		return false
	da.list_dir_begin()
	var n := da.get_next()
	var found_dir := false
	var found_001 := false
	while n != "":
		var lower := n.to_lower()
		if lower == "data.dir":
			found_dir = true
		elif lower == "data.001":
			found_001 = true
		n = da.get_next()
	return found_dir and found_001


static func _search_under(path: String, depth: int) -> String:
	if _has_data_dir(path):
		return path
	if depth <= 0:
		return ""
	var da := DirAccess.open(path)
	if da == null:
		return ""
	da.list_dir_begin()
	var n := da.get_next()
	var preferred: Array = []
	var other: Array = []
	while n != "":
		if da.current_is_dir() and n != "." and n != "..":
			var sub := path.path_join(n)
			if n.to_lower() == "trekcd":
				preferred.append(sub)
			else:
				other.append(sub)
		n = da.get_next()
	for sub in preferred + other:
		var hit := _search_under(str(sub), depth - 1)
		if not hit.is_empty():
			return hit
	return ""


static func find_game_root() -> String:
	for c in candidate_dirs():
		var found := _search_under(c, 3)
		if not found.is_empty():
			return found
	return ""
