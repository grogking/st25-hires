class_name StArchive
extends RefCounted
## DATA.DIR / DATA.001 / DATA.RUN reader. Independent of ScummVM C++.

var root_path: String = ""
var entries: Dictionary = {} ## upper name -> {offset:int, file_count:int}
var _data_001: PackedByteArray = PackedByteArray()
var _data_run: PackedByteArray = PackedByteArray()
var loaded: bool = false


static func _files_lower(path: String) -> Dictionary:
	var out := {}
	var da := DirAccess.open(path)
	if da == null:
		return out
	da.list_dir_begin()
	var n := da.get_next()
	while n != "":
		if not da.current_is_dir():
			out[n.to_lower()] = path.path_join(n)
		n = da.get_next()
	return out


static func parse_dir(data: PackedByteArray) -> Array:
	var list: Array = []
	if data.size() < 14:
		return list
	var i := 0
	while i + 14 <= data.size():
		var name := _c_string(data, i, 8)
		if name.is_empty():
			i += 14
			continue
		var ext := _c_string(data, i + 8, 3)
		var filename := name if ext.is_empty() else "%s.%s" % [name, ext]
		var off: int = data[i + 11] + (data[i + 12] << 8) + (data[i + 13] << 16)
		var rec := {}
		if off & (1 << 23):
			rec["file_count"] = (off >> 16) & 0x7F
			rec["offset"] = off & 0xFFFF
		else:
			rec["file_count"] = 1
			rec["offset"] = off & 0xFFFFFF
		rec["name"] = filename
		list.append(rec)
		i += 14
	return list


static func _c_string(data: PackedByteArray, pos: int, n: int) -> String:
	var bytes := PackedByteArray()
	for i in range(n):
		var b: int = data[pos + i]
		if b == 0:
			break
		bytes.append(b)
	return bytes.get_string_from_ascii()


static func sequential_data001_offset(data_run: PackedByteArray, run_offset: int, file_index: int) -> int:
	if file_index < 0 or run_offset + 3 > data_run.size():
		return -1
	var pos := run_offset
	var offset: int = data_run[pos] + (data_run[pos + 1] << 8) + (data_run[pos + 2] << 16)
	pos += 3
	for _i in range(file_index):
		if pos + 2 > data_run.size():
			return -1
		offset += data_run[pos] | (data_run[pos + 1] << 8)
		pos += 2
	return offset


static func extract_file(data_001: PackedByteArray, offset: int) -> PackedByteArray:
	if offset < 0 or offset + 4 > data_001.size():
		return PackedByteArray()
	var uncmp: int = data_001[offset] | (data_001[offset + 1] << 8)
	var cmp_size: int = data_001[offset + 2] | (data_001[offset + 3] << 8)
	if offset + 4 + cmp_size > data_001.size():
		return PackedByteArray()
	var payload := data_001.slice(offset + 4, offset + 4 + cmp_size)
	return StLzss.decode(payload, uncmp)


func open_dir(path: String) -> bool:
	root_path = path
	var names := _files_lower(path)
	if not names.has("data.dir") or not names.has("data.001"):
		return false
	var dir_bytes := FileAccess.get_file_as_bytes(names["data.dir"])
	_data_001 = FileAccess.get_file_as_bytes(names["data.001"])
	if names.has("data.run"):
		_data_run = FileAccess.get_file_as_bytes(names["data.run"])
	entries.clear()
	for rec in parse_dir(dir_bytes):
		entries[str(rec["name"]).to_upper()] = rec
	loaded = not entries.is_empty()
	return loaded


func has(name: String) -> bool:
	return entries.has(name.to_upper())


func file_count(name: String) -> int:
	var key := name.to_upper()
	if not entries.has(key):
		return 0
	return int(entries[key]["file_count"])


func load_file(name: String, file_index: int = 0) -> PackedByteArray:
	var key := name.to_upper()
	if not entries.has(key):
		return PackedByteArray()
	var rec: Dictionary = entries[key]
	var count: int = int(rec["file_count"])
	var offset: int = int(rec["offset"])
	if count == 1:
		if file_index != 0:
			return PackedByteArray()
		return extract_file(_data_001, offset)
	if file_index < 0 or file_index >= count or _data_run.is_empty():
		return PackedByteArray()
	var data001_off := sequential_data001_offset(_data_run, offset, file_index)
	if data001_off < 0:
		return PackedByteArray()
	return extract_file(_data_001, data001_off)
