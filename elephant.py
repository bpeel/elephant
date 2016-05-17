#!/usr/bin/env python3

import gi

gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg

import cairo
import math
import subprocess
import shutil
import os
import sys

SCALE = 4
WIDTH = 1920
HEIGHT = 1080

HEAD_CENTER = [1008, 437]
HEAD_ROTATION = 10.0 * math.pi / 180.0
HEAD_ROTATION_TIME = 1.0
FRAME_RATE = 30

BALLOON_NOSE_POINT = (1019, 221)

ELEPHANT_FRAMES = ["layer2", "g4209", "layer1"]

FOREGROUND_SIZE = 4038.071

MEZGROUND_SIZE = 3070

BALLOON_DISAPPEAR_TIME = 3.0
# Pixels per second per second
BALLOON_ACCELERATION = HEIGHT / 2

def rotate_point(angle, x, y):
    s = math.sin(angle)
    c = math.cos(angle)
    return (x * c - y * s,
            x * s + y * c)

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

if len(sys.argv) == 2 and sys.argv[1] == '-p':
    play_video = True
elif len(sys.argv) == 1:
    play_video = False
else:
    sys.stderr.write("usage: {} [-p]\n".format(sys.argv[0]))
    sys.exit(1)

elephant_svg = Rsvg.Handle.new_from_file('elephant.svg')

surface = cairo.ImageSurface(cairo.FORMAT_RGB24,
                             WIDTH // SCALE,
                             HEIGHT // SCALE)
cr = cairo.Context(surface)
cr.scale(1.0 / SCALE, 1.0 / SCALE)

input_args = ["-f", "rawvideo",
              "-pixel_format", "rgb24",
              "-video_size", "{}x{}".format(surface.get_width(),
                                            surface.get_height()),
              "-framerate", str(FRAME_RATE),
              "-i", "-"]
output_args = ["-c:v", "libvpx",
               "-b:v", "3M",
               "-y",
               "elephant-no-sound.webm"]

if play_video:
    args = ['ffplay'] + input_args
else:
    args = ['ffmpeg'] + input_args + output_args

ffout = subprocess.Popen(args, stdin = subprocess.PIPE)

for frame_num in range(800):
    elapsed_time = frame_num / FRAME_RATE

    camera_pos = elapsed_time * 300

    render_sub(elephant_svg, cr, "#layer3")

    mezground_pos = camera_pos
    inner_pos = mezground_pos % MEZGROUND_SIZE
    cr.save()
    cr.translate(-inner_pos, 0.0)
    render_sub(elephant_svg, cr, "#layer6")
    cr.translate(MEZGROUND_SIZE, 0.0)
    render_sub(elephant_svg, cr, "#layer6")
    cr.restore()

    rotation_sin = math.sin(elapsed_time * math.pi * 2.0 /
                            HEAD_ROTATION_TIME)
    rotation_angle = HEAD_ROTATION * rotation_sin

    frame_num = min(len(ELEPHANT_FRAMES) - 1,
                    max(int((rotation_sin / 2.0 + 0.5) *
                        (len(ELEPHANT_FRAMES) - 1) + 0.5), 0))

    render_sub(elephant_svg, cr, "#" + ELEPHANT_FRAMES[frame_num])

    cr.save()
    rotate_about(cr, *HEAD_CENTER, angle = rotation_angle)
    render_sub(elephant_svg, cr, "#layer4")
    cr.restore()

    if elapsed_time < BALLOON_DISAPPEAR_TIME:
        nose_point = rotate_point(-rotation_angle,
                                  BALLOON_NOSE_POINT[0] - HEAD_CENTER[0],
                                  BALLOON_NOSE_POINT[1] - HEAD_CENTER[1])
        balloon_pos = (HEAD_CENTER[0] + nose_point[0],
                       HEIGHT - 1 - (HEAD_CENTER[1] + nose_point[1]))
        balloon_base = (balloon_pos[0] + camera_pos, balloon_pos[1])
    else:
        time_delta = elapsed_time - BALLOON_DISAPPEAR_TIME
        y_offset = time_delta * time_delta * BALLOON_ACCELERATION / 2.0
        balloon_pos = (balloon_base[0] - camera_pos, balloon_base[1] - y_offset)

    cr.save()
    cr.translate(*balloon_pos)
    render_sub(elephant_svg, cr, "#layer7")
    cr.restore()

    foreground_pos = camera_pos * 1.4
    inner_pos = foreground_pos % FOREGROUND_SIZE
    cr.save()
    cr.translate(-inner_pos, 0.0)
    render_sub(elephant_svg, cr, "#layer5")
    cr.translate(FOREGROUND_SIZE, 0.0)
    render_sub(elephant_svg, cr, "#layer5")
    cr.restore()

    write_frame(ffout, surface)

ffout.stdin.close()

if ffout.wait() != 0:
    raise Exception("convert failed")

if not play_video:
    ret = subprocess.call(["ffmpeg",
                           "-i", "elephant-no-sound.webm",
                           "-i", "021914bgm2(happytune).mp3",
                           "-shortest",
                           "-c:v", "copy",
                           "-c:a", "libvorbis",
                           "-aq", "4",
                           "-y",
                           "elephant.webm"])
    if ret != 0:
        raise Exception("ffmpeg failed")
