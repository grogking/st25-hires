class_name StLzss
extends RefCounted
## LZSS used by DATA.001 (N=0x1000, threshold 3). Independent of ScummVM.

const N := 0x1000
const THRESHOLD := 3


static func decode(data: PackedByteArray, uncompressed_size: int) -> PackedByteArray:
	var hist := PackedByteArray()
	hist.resize(N)
	var bufpos := 0
	var out := PackedByteArray()
	out.resize(uncompressed_size)
	var out_i := 0
	var i := 0
	var length := data.size()

	while i < length and out_i < uncompressed_size:
		var flagbyte := data[i]
		i += 1
		for bit in range(8):
			if out_i >= uncompressed_size or i >= length:
				break
			if (flagbyte & (1 << bit)) == 0:
				if i + 1 >= length:
					break
				var offsetlen: int = data[i] | (data[i + 1] << 8)
				i += 2
				var run: int = (offsetlen & 0xF) + THRESHOLD
				var offset: int = (bufpos - (offsetlen >> 4)) & (N - 1)
				for j in range(run):
					var tempa: int = hist[(offset + j) & (N - 1)]
					out[out_i] = tempa
					out_i += 1
					hist[bufpos] = tempa
					bufpos = (bufpos + 1) & (N - 1)
					if out_i >= uncompressed_size:
						break
			else:
				var literal: int = data[i]
				i += 1
				out[out_i] = literal
				out_i += 1
				hist[bufpos] = literal
				bufpos = (bufpos + 1) & (N - 1)

	if out_i != uncompressed_size:
		push_error("LZSS size mismatch: expected %d, got %d" % [uncompressed_size, out_i])
		return PackedByteArray()
	return out
