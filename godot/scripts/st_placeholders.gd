class_name StPlaceholders
extends RefCounted
## Obvious stand-in cards used when TREKCD is not on this machine.


static func star_image() -> Image:
	var img := Image.create(3, 3, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	img.set_pixel(1, 1, Color(1, 1, 1, 1))
	img.set_pixel(0, 1, Color(0.55, 0.55, 0.7, 1))
	img.set_pixel(2, 1, Color(0.55, 0.55, 0.7, 1))
	img.set_pixel(1, 0, Color(0.55, 0.55, 0.7, 1))
	img.set_pixel(1, 2, Color(0.55, 0.55, 0.7, 1))
	return img


static func planet_image(diameter: int = 180) -> Image:
	var img := Image.create(diameter, diameter, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var r := diameter * 0.5
	var bayer := PackedInt32Array([0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5])
	var bands := PackedColorArray([
		Color(0.28, 0.04, 0.04),
		Color(0.48, 0.07, 0.06),
		Color(0.68, 0.14, 0.10),
		Color(0.82, 0.26, 0.16),
	])
	for y in range(diameter):
		for x in range(diameter):
			var dx := (x + 0.5 - r) / r
			var dy := (y + 0.5 - r) / r
			var d2 := dx * dx + dy * dy
			if d2 > 1.0:
				continue
			var z := sqrt(1.0 - d2)
			var light := clampf(-0.35 * dx - 0.12 * dy + 0.92 * z, 0.0, 1.0)
			var marble := sin(dx * 6.5 + dy * 3.2 + sin(dy * 8.0) * 1.4)
			var shade := light * 0.78 + 0.12 + marble * 0.07
			var t := float(bayer[(y & 3) * 4 + (x & 3)]) / 16.0
			var band := clampi(int(floor(shade * 4.0 + t * 0.35)), 0, 3)
			img.set_pixel(x, y, bands[band])
	return img


static func enterprise_image() -> Image:
	## Side-on silhouette flying to the right. Geometric stand-in, not game art.
	var w := 112
	var h := 36
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var hull := Color(0.78, 0.80, 0.84)
	var dark := Color(0.42, 0.44, 0.50)
	var nacelle := Color(0.70, 0.72, 0.78)
	var red := Color(0.75, 0.18, 0.16)
	# Secondary hull (aft, left)
	_fill_ellipse(img, 38, 22, 22, 7, hull)
	_fill_rect(img, 18, 20, 22, 5, hull)
	# Neck
	_fill_rect(img, 52, 14, 8, 10, dark)
	# Saucer (forward / right)
	_fill_ellipse(img, 78, 14, 28, 9, hull)
	_fill_ellipse(img, 78, 14, 10, 3, dark)
	# Impulse glow
	_fill_rect(img, 14, 21, 4, 3, red)
	# Pylon + nacelle (top)
	_fill_rect(img, 40, 8, 4, 8, dark)
	_fill_ellipse(img, 44, 6, 26, 4, nacelle)
	_fill_rect(img, 18, 5, 10, 3, nacelle)
	# Nacelle cap
	img.set_pixel(70, 6, red)
	img.set_pixel(69, 6, red)
	return img


static func _fill_rect(img: Image, x: int, y: int, w: int, h: int, c: Color) -> void:
	for yy in range(y, y + h):
		for xx in range(x, x + w):
			if xx >= 0 and yy >= 0 and xx < img.get_width() and yy < img.get_height():
				img.set_pixel(xx, yy, c)


static func _fill_ellipse(img: Image, cx: int, cy: int, rx: int, ry: int, c: Color) -> void:
	for yy in range(cy - ry, cy + ry + 1):
		for xx in range(cx - rx, cx + rx + 1):
			if xx < 0 or yy < 0 or xx >= img.get_width() or yy >= img.get_height():
				continue
			var dx := float(xx - cx) / float(max(rx, 1))
			var dy := float(yy - cy) / float(max(ry, 1))
			if dx * dx + dy * dy <= 1.0:
				img.set_pixel(xx, yy, c)
