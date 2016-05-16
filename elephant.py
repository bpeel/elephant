#!/usr/bin/env python3

import gi

gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

import cairo
import math
import subprocess
import shutil
import os

SCALE = 4
WIDTH = 1920
HEIGHT = 1080

HEAD_CENTER = [1008, 437]

def render_sub(rsvg, cr, id_name):
    res = rsvg.render_cairo_sub(cr, id_name)
    if not res:
        raise Exception("Failed to render {}".format(id_name))

def rotate_about(cr, cx, cy, angle):
    cy = HEIGHT - 1 - cy
    cr.translate(cx, cy)
    cr.rotate(angle)
    cr.translate(-cx, -cy)

def write_frame(ffout, surface):
    buf = b'\0' * 1024
    surface.write_to_png('result.png')
    sp = subprocess.Popen(["convert", "result.png", "rgb:-"],
                          stdout = subprocess.PIPE)
    shutil.copyfileobj(sp.stdout, ffout.stdin)
    if sp.wait() != 0:
        raise Exception("convert failed")
    os.unlink('result.png')

elephant_svg = Rsvg.Handle.new_from_file('elephant.svg')

surface = cairo.ImageSurface(cairo.FORMAT_RGB24,
                             WIDTH // SCALE,
                             HEIGHT // SCALE)
cr = cairo.Context(surface)
cr.scale(1.0 / SCALE, 1.0 / SCALE)

ffout = subprocess.Popen(["ffmpeg",
                          "-f", "rawvideo",
                          "-pixel_format", "rgb24",
                          "-video_size", "{}x{}".format(surface.get_width(),
                                                        surface.get_height()),
                          "-framerate", "30",
                          "-i", "-",
                          "-c:v", "libvpx",
                          "-b:v", "3M",
                          "-y",
                          "elephant.webm"],
                         stdin = subprocess.PIPE)

for frame_num in range(100):
    cr.set_source_rgb(1, 1, 1)
    cr.paint()

    render_sub(elephant_svg, cr, "#layer1")

    cr.save()
    rotate_about(cr, *HEAD_CENTER, angle = frame_num * math.pi * 2.0 / 60.0)
    render_sub(elephant_svg, cr, "#layer4")
    cr.restore()

    write_frame(ffout, surface)

ffout.stdin.close()

if ffout.wait() != 0:
    raise Exception("convert failed")
