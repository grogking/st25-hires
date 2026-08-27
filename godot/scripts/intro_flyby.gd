class_name IntroFlyby
extends Node3D
## GOG-style opening flyby: starfield, red planet, side-on Enterprise.
## Native space is 320x200. 1 world unit = 1 native pixel. Origin = screen center.

const TICK_HZ := 18.2
const TICK_DT := 1.0 / TICK_HZ
const LOOP_TICKS := 92
const STAR_COUNT := 58

## GOG beats (approx frame numbers at 18.2 Hz): stars, planet-pass, ship leaves.
const KEY_STARS := 0
const KEY_PLANET_IN := 12
const KEY_SHIP_IN := 16
const KEY_MID := 28
const KEY_EXIT := 43
const KEY_SPECK := 50

var archive: StArchive
var using_placeholders := true
var status_text := "placeholder sprites — set ST25_GAME_DIR to TREKCD"
var _have_game_stars := false
var _have_game_planet := false
var _have_game_ship := false

var _tick := 0
var _accum := 0.0
var _palette: PackedColorArray

var _stars_root: Node3D
var _planet: Sprite3D
var _planet_base_scale := 1.0
var _ship: Sprite3D
var _dump_dir := ""
var _dumped: Dictionary = {}
var _dump_wanted := {5: true, 20: true, 30: true, 43: true, 50: true}


func setup(p_archive: StArchive) -> void:
	archive = p_archive
	_palette = _load_palette()
	_build_camera_world()
	_spawn_starfield()
	_spawn_planet()
	_spawn_ship()
	_layout_tick(0)
	_dump_dir = OS.get_environment("ST25_DUMP_DIR")


func _process(delta: float) -> void:
	_accum += delta
	# One sim tick per frame so dump/debug cannot skip beats on a hitch.
	if _accum >= TICK_DT:
		_accum = minf(_accum - TICK_DT, TICK_DT)
		_tick += 1
		if _tick >= LOOP_TICKS and _dump_dir.is_empty():
			_tick = 0
		_layout_tick(_tick)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept") or (event is InputEventKey and event.pressed and event.keycode == KEY_R):
		_tick = 0
		_accum = 0.0
		_layout_tick(0)
		get_viewport().set_input_as_handled()


func _build_camera_world() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0, 0, 0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(1, 1, 1)
	env.ambient_light_energy = 1.0
	env.glow_enabled = false
	env.ssao_enabled = false
	env.ssil_enabled = false
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	add_child(world_env)

	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = float(StBitmap.SCREEN_HEIGHT)
	cam.near = 0.1
	cam.far = 200.0
	cam.position = Vector3(0, 0, 80)
	cam.current = true
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	add_child(cam)


func _sprite(tex: Texture2D, priority: int) -> Sprite3D:
	var s := Sprite3D.new()
	s.texture = tex
	s.centered = true
	s.pixel_size = 1.0
	s.shaded = false
	s.double_sided = true
	s.alpha_cut = SpriteBase3D.ALPHA_CUT_DISABLED
	s.transparent = true
	s.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	s.render_priority = priority
	return s


func _tex_from_image(img: Image) -> ImageTexture:
	return ImageTexture.create_from_image(img)


func _load_palette() -> PackedColorArray:
	if archive == null or not archive.loaded:
		return PackedColorArray()
	for name in ["BRIDGE.PAL", "PALETTE.PAL"]:
		if archive.has(name):
			var pal := StBitmap.parse_palette(archive.load_file(name))
			if pal.size() == 256:
				return pal
	return PackedColorArray()


func _frame_texture(frame: StBitmap.Frame) -> Texture2D:
	if frame == null:
		return null
	if _palette.is_empty():
		return null
	return _tex_from_image(frame.to_image(_palette))


func _spawn_starfield() -> void:
	_stars_root = Node3D.new()
	_stars_root.name = "Starfield"
	add_child(_stars_root)
	var textures: Array = []
	if archive and archive.loaded and archive.has("STARS.SHP") and not _palette.is_empty():
		var frames: Array = StBitmap.parse_shp_frames(archive.load_file("STARS.SHP"))
		for fr in frames:
			var tex := _frame_texture(fr)
			if tex:
				textures.append(tex)
	if textures.is_empty():
		textures.append(_tex_from_image(StPlaceholders.star_image()))
	else:
		_have_game_stars = true

	var rng := RandomNumberGenerator.new()
	rng.seed = 25
	for i in range(STAR_COUNT):
		var spr := _sprite(textures[rng.randi() % textures.size()], -8)
		var x := rng.randf_range(-158.0, 158.0)
		var y := rng.randf_range(-98.0, 98.0)
		var z := rng.randf_range(-40.0, -8.0)
		spr.position = Vector3(x, y, z)
		var dim := rng.randf_range(0.45, 1.0)
		spr.modulate = Color(dim, dim, dim, 1)
		_stars_root.add_child(spr)


func _spawn_planet() -> void:
	var tex: Texture2D = null
	if archive and archive.loaded and not _palette.is_empty():
		for name in ["PLANET.SHP", "PLANET.BMP"]:
			if not archive.has(name):
				continue
			var blob := archive.load_file(name)
			var frames: Array = StBitmap.parse_shp_frames(blob) if name.ends_with(".SHP") else []
			var frame: StBitmap.Frame = frames[0] if frames.size() > 0 else StBitmap.parse_bitmap(blob)
			tex = _frame_texture(frame)
			if tex:
				_have_game_planet = true
				break
	if tex == null:
		tex = _tex_from_image(StPlaceholders.planet_image(180))
	_planet = _sprite(tex, -2)
	_planet.name = "Planet"
	# Scale so the disk is a large GOG-style body (~210 px).
	var max_dim := maxf(float(tex.get_width()), float(tex.get_height()))
	_planet_base_scale = 210.0 / max(max_dim, 1.0)
	_planet.scale = Vector3(_planet_base_scale, _planet_base_scale, 1)
	add_child(_planet)


func _spawn_ship() -> void:
	var tex: Texture2D = null
	if archive and archive.loaded and not _palette.is_empty():
		var frame := _pick_side_enterprise()
		tex = _frame_texture(frame)
		if tex:
			_have_game_ship = true
	if tex == null:
		tex = _tex_from_image(StPlaceholders.enterprise_image())
	_ship = _sprite(tex, 4)
	_ship.name = "Enterprise"
	add_child(_ship)
	using_placeholders = not (_have_game_ship or _have_game_planet)
	if archive == null or not archive.loaded:
		status_text = "placeholder sprites — set ST25_GAME_DIR to TREKCD"
	elif using_placeholders:
		status_text = "TREKCD found but intro sprites missing — placeholders"
	else:
		status_text = "loaded %s" % archive.root_path


func _yaw_suffixes(yaw_i: int) -> PackedStringArray:
	var n := yaw_i * 11
	var out := PackedStringArray(["%02d" % n])
	# Some notes list the last yaw band as 61 rather than 66.
	if yaw_i == 6:
		out.append("61")
	return out


func _pick_side_enterprise() -> StBitmap.Frame:
	## Yaw band is ENT{00,11,...,66}.R3S; fileIndex is elevation (equator ~ 3).
	## Side-on profile is typically the widest sprite on the equatorial ring.
	var best: StBitmap.Frame = null
	var best_score := -1.0
	for yaw in [3, 2, 4, 1, 5, 0, 6]:
		for suffix in _yaw_suffixes(yaw):
			var fname := "ENT%s.R3S" % suffix
			if not archive.has(fname):
				continue
			var count := archive.file_count(fname)
			var elevs := [3, 2, 4]
			if count > 0:
				for e in range(mini(count, 7)):
					if not elevs.has(e):
						elevs.append(e)
			for elev in elevs:
				if elev >= count:
					continue
				var raw := archive.load_file(fname, elev)
				var frame := StBitmap.parse_r3s(raw)
				if frame == null:
					continue
				var equator := 1.0 - absi(elev - 3) * 0.15
				var yaw_side := 1.0 - absi(yaw - 3) * 0.12
				var score := float(frame.width) * equator * yaw_side
				if score > best_score:
					best_score = score
					best = frame
			if best != null and yaw == 3:
				return best
	return best


func _layout_tick(tick: int) -> void:
	# Full 320x200 — no ScummVM-style grey subtitle bar.
	var planet_visible := tick >= KEY_PLANET_IN and tick < KEY_SPECK
	_planet.visible = planet_visible
	var p_scale := 1.0
	var p_y := -20.0
	if tick < KEY_SHIP_IN:
		p_scale = 0.72
		p_y = -18.0
	elif tick < KEY_EXIT:
		var u := inverse_lerp(KEY_SHIP_IN, KEY_EXIT, tick)
		p_scale = lerp(0.85, 1.25, u)
		p_y = lerp(-28.0, -72.0, u)
	else:
		p_scale = 1.35
		p_y = -88.0
	var base := _planet_base_scale
	_planet.scale = Vector3(base * p_scale, base * p_scale, 1)
	_planet.position = Vector3(10, p_y, -12)

	var ship_tex_w: float = float(_ship.texture.get_width()) if _ship.texture else 112.0
	var close_scale: float = 90.0 / maxf(ship_tex_w, 1.0)

	var x := -200.0
	var y := 22.0
	var sc: float = close_scale * 0.35
	var vis := tick >= KEY_SHIP_IN

	if tick < KEY_SHIP_IN:
		vis = false
	elif tick < KEY_MID:
		var u := inverse_lerp(KEY_SHIP_IN, KEY_MID, tick)
		x = lerp(-170.0, -10.0, u)
		y = lerp(18.0, 22.0, u)
		sc = lerp(close_scale * 0.55, close_scale, u)
	elif tick < KEY_EXIT:
		var u := inverse_lerp(KEY_MID, KEY_EXIT, tick)
		x = lerp(-10.0, 130.0, u)
		y = lerp(22.0, 28.0, u)
		sc = close_scale
	elif tick < KEY_SPECK:
		var u := inverse_lerp(KEY_EXIT, KEY_SPECK, tick)
		x = lerp(130.0, 175.0, u)
		y = lerp(28.0, 20.0, u)
		sc = lerp(close_scale, close_scale * 0.35, u)
	else:
		var u := clampf(inverse_lerp(KEY_SPECK, LOOP_TICKS - 8, tick), 0.0, 1.0)
		x = lerp(40.0, 90.0, u)
		y = lerp(8.0, 18.0, u)
		sc = lerp(close_scale * 0.12, close_scale * 0.04, u)
		vis = true

	_ship.visible = vis
	_ship.position = Vector3(x, y, 4)
	_ship.scale = Vector3(sc, sc, 1)


func maybe_dump_native(viewport: SubViewport) -> bool:
	if _dump_dir.is_empty():
		return false
	if not _dump_wanted.has(_tick) or _dumped.has(_tick):
		return false
	DirAccess.make_dir_recursive_absolute(_dump_dir)
	var img := viewport.get_texture().get_image()
	if img == null:
		return false
	var path := _dump_dir.path_join("native_%03d.png" % _tick)
	img.save_png(path)
	_dumped[_tick] = true
	print("ST25 dumped ", path)
	return _dumped.size() >= _dump_wanted.size()
