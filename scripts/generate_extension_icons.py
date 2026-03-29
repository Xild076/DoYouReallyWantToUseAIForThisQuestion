import os
import struct
import zlib

OUT_DIR = "icons"
SIZES = (16, 32, 48, 96, 128)


def pixel_color(x, y, size):
    pad = max(1, size // 16)
    if x < pad or y < pad or x >= size - pad or y >= size - pad:
        return (17, 17, 17)

    cx = size // 2
    cy = size // 2
    dx = x - cx
    dy = y - cy
    dist2 = dx * dx + dy * dy

    r_outer = (size * 5) // 12
    r_inner = (size * 3) // 12

    if r_inner * r_inner <= dist2 <= r_outer * r_outer:
        return (227, 56, 27)

    if dist2 <= (size // 10) ** 2:
        return (17, 17, 17)

    return (245, 243, 236)


def png_chunk(tag, data):
    return (
        struct.pack("!I", len(data))
        + tag
        + data
        + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def write_png(path, size):
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!IIBBBBB", size, size, 8, 2, 0, 0, 0)

    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            row.extend(pixel_color(x, y, size))
        rows.append(b"\x00" + bytes(row))

    idat = zlib.compress(b"".join(rows), 9)
    data = signature + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(data)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for size in SIZES:
        path = os.path.join(OUT_DIR, f"icon{size}.png")
        write_png(path, size)
        print(f"[+] wrote {path}")


if __name__ == "__main__":
    main()
