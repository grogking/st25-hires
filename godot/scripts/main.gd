extends Control
## Window host: 320x200 SubViewport, nearest-neighbor blit into a 4:3 window.
## Project stretch is canvas_items (not viewport) so a later scaler shader can hook here.

const NATIVE_W := 320
const NATIVE_H := 200

var _sv: SubViewport
var _flyby: IntroFlyby
var _status: Label
var _blit: TextureRect


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	var bg := ColorRect.new()
	bg.color = Color(0, 0, 0)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_sv = SubViewport.new()
	_sv.name = "Native320x200"
	_sv.size = Vector2i(NATIVE_W, NATIVE_H)
	_sv.own_world_3d = true
	_sv.transparent_bg = false
	_sv.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_sv.msaa_2d = Viewport.MSAA_DISABLED
	_sv.msaa_3d = Viewport.MSAA_DISABLED
	_sv.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	_sv.use_debanding = false
	_sv.snap_2d_transforms_to_pixel = true
	_sv.snap_2d_vertices_to_pixel = true
	_sv.handle_input_locally = false
	_sv.disable_3d = false
	add_child(_sv)

	_blit = TextureRect.new()
	_blit.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_blit.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_blit.stretch_mode = TextureRect.STRETCH_SCALE
	_blit.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_blit.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_blit.texture = _sv.get_texture()
	add_child(_blit)

	_flyby = IntroFlyby.new()
	_sv.add_child(_flyby)

	_status = Label.new()
	_status.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_status.position = Vector2(8, 6)
	_status.add_theme_font_size_override("font_size", 13)
	_status.add_theme_color_override("font_color", Color(0.92, 0.82, 0.25))
	_status.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	_status.add_theme_constant_override("outline_size", 4)
	add_child(_status)

	var root := StPaths.find_game_root()
	var archive := StArchive.new()
	if not root.is_empty() and archive.open_dir(root):
		print("ST25 archive: ", root, " files=", archive.entries.size())
	else:
		print("ST25 archive not found; using placeholders. Set ST25_GAME_DIR to TREKCD.")
		archive = StArchive.new()
	_flyby.setup(archive)
	_status.text = _flyby.status_text
	if not OS.get_environment("ST25_DUMP_DIR").is_empty():
		_watch_dumps()


func _watch_dumps() -> void:
	var frames := 0
	while frames < 2400:
		await RenderingServer.frame_post_draw
		frames += 1
		_status.text = _flyby.status_text
		if _flyby.maybe_dump_native(_sv):
			get_tree().quit()
			return
	push_warning("ST25 dump timed out after 2400 frames")
	get_tree().quit()
