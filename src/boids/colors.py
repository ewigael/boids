"""Small module to manipulate color values"""

import colorsys
from random import uniform


def hex_to_hls(hex_color):
    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255

    return colorsys.rgb_to_hls(r, g, b)


def hls_to_hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, l, s)

    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def small_change_hex(hex_color):
    """Very slightly change the hue, saturation and brightness of an hexadecimal color string.
    Returns an hex color string"""

    hue, lightness, saturation = hex_to_hls(hex_color)

    hue += uniform(-0.05, 0.05)
    saturation += uniform(-0.08, 0.08)
    lightness += uniform(-0.08, 0.08)

    hue %= 1.0
    saturation = max(0.0, min(1.0, saturation))
    lightness = max(0.0, min(1.0, lightness))

    return hls_to_hex(hue, saturation, lightness)
