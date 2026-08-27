class_name StBitmap
extends RefCounted
## Interplay custom BMP / SHP / R3S (not Windows BMP).

const SCREEN_WIDTH := 320
const SCREEN_HEIGHT := 200
const R3S_HEADER_SIZE := 36


class Frame:
	var xoffset: int
	var yoffset: int
	var width: int
	var height: int
	var pixels: PackedByteArray

	func to_image(palette: PackedColorArray) -> Image:
		var rgba := PackedByteArray()
		rgba.resize(width * height * 4)
		for i in range(width * height):
			var idx := pixels[i]
			var o := i * 4
			if idx == 0 or idx >= palette.size():
				rgba[o] = 0
				rgba[o + 1] = 0
				rgba[o + 2] = 0
				rgba[o + 3] = 0
			else:
				var c := palette[idx]
				rgba[o] = int(round(c.r * 255.0))
				rgba[o + 1] = int(round(c.g * 255.0))
				rgba[o + 2] = int(round(c.b * 255.0))
				rgba[o + 3] = 255
		return Image.create_from_data(width, height, false, Image.FORMAT_RGBA8, rgba)


static func u16(data: PackedByteArray, pos: int) -> int:
	return data[pos] | (data[pos + 1] << 8)


static func parse_bitmap(data: PackedByteArray, pos: int = 0) -> Frame:
	if pos + 8 > data.size():
		return null
	var frame := Frame.new()
	frame.xoffset = u16(data, pos)
	frame.yoffset = u16(data, pos + 2)
	frame.width = u16(data, pos + 4)
	frame.height = u16(data, pos + 6)
	var need := frame.width * frame.height
	if frame.width <= 0 or frame.height <= 0 or pos + 8 + need > data.size():
		return null
	frame.pixels = data.slice(pos + 8, pos + 8 + need)
	return frame


static func parse_shp_frames(data: PackedByteArray) -> Array:
	var frames: Array = []
	var pos := 0
	while pos + 8 <= data.size():
		var width := u16(data, pos + 4)
		var height := u16(data, pos + 6)
		var need := 8 + width * height
		if width == 0 or height == 0 or pos + need > data.size():
			break
		var frame := parse_bitmap(data, pos)
		if frame == null:
			break
		frames.append(frame)
		pos += need
	return frames


static func parse_r3s(data: PackedByteArray) -> Frame:
	if data.size() < R3S_HEADER_SIZE + 8:
		return null
	return parse_bitmap(data, R3S_HEADER_SIZE)


static func parse_palette(data: PackedByteArray) -> PackedColorArray:
	var pal := PackedColorArray()
	pal.resize(256)
	if data.size() < 256 * 3:
		return pal
	for i in range(256):
		var r := data[i * 3] << 2
		var g := data[i * 3 + 1] << 2
		var b := data[i * 3 + 2] << 2
		pal[i] = Color8(r, g, b, 255)
	return pal
