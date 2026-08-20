"""Small module to manipulate color values"""

import colorsys
import math
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


def value_to_color_gradient_log(
    value, min_value, max_value, color_start="#324D4C", color_end="#FF0000"
):
    """Return color value as part of a gradient defined in parameters through logarythmic interpolation"""

    value = max(min_value, min(value, max_value))

    hls_start = hex_to_hls(color_start)
    hls_end = hex_to_hls(color_end)

    t = (math.log(value) - math.log(min_value)) / (
        math.log(max_value) - math.log(min_value)
    )

    h = hls_start[0] + (hls_end[0] - hls_start[0]) * t
    l = hls_start[1] + (hls_end[1] - hls_start[1]) * t
    s = hls_start[2] + (hls_end[2] - hls_start[2]) * t

    return hls_to_hex(h, l, s)


def value_to_color_gradient_linear(
    value, min_value, max_value, color_start="#5B7341", color_end="#FF0000"
):
    """Return color value as part of a gradient defined in parameters through linear interpolation"""

    value = max(min_value, min(value, max_value))

    hls_start = hex_to_hls(color_start)
    hls_end = hex_to_hls(color_end)

    t = (value - min_value) / (max_value - min_value)

    h = hls_start[0] + (hls_end[0] - hls_start[0]) * t
    l = hls_start[1] + (hls_end[1] - hls_start[1]) * t
    s = hls_start[2] + (hls_end[2] - hls_start[2]) * t

    return hls_to_hex(h, l, s)
