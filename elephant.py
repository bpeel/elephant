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

SCALE = 1
WIDTH = 1920
HEIGHT = 1080

HEAD_CENTER = [608, 437]
HEAD_ROTATION = 10.0 * math.pi / 180.0
HEAD_ROTATION_TIME = 1.0
FRAME_RATE = 30

BALLOON_NOSE_POINT = (619, 221)

RHINO_TAIL_POINT = (1496, 651)
RHINO_TAIL_ROTATION = 5.0 * math.pi / 180.0
RHINO_POS = WIDTH * 1.5 + 900

RHINO_ENTRY_START = -2343
RHINO_ENTRY_END = -1477

ALLIGATOR_POS = WIDTH * 3.0 + 900
ALLIGATOR_HEAD_POINT = (1026, 357)
ALLIGATOR_ROTATION = 30.0 * math.pi / 180.0
ALLIGATOR_ROTATE_TIME = (25, 3)

ALLIGATOR_ENTRY_START = 1115
ENTRY_TIME = (37, 3)

MONKEY_POS = WIDTH * 4.0 + 900
MONKEY_HAND_POINT = (1150, 870)
MONKEY_HOLD_POINT = (1015, 395)
MONKEY_ROTATION = 10.0 * math.pi / 180.0

ELEPHANT_FRAMES = ["layer2", "g4209", "layer1"]

FOREGROUND_SIZE = 4038.071

MEZGROUND_SIZE = 3134

BALLOON_DISAPPEAR_TIME = 6.0
# Pixels per secqond per second
BALLOON_ACCELERATION = HEIGHT / 2

BALLOON_PASSOVER_TIME = (35, 1)

PAUSES = [(14, 3), (25, 3), (35, 300)]

TITLE_TIME = 3
TITLE_FADE_TIME = 0.5

CREDIT_TIME = 3
CREDIT_SLIDE_TIME = 1
N_CREDITS = 5

AUDIO_TIMES = [ ( 0, "title.flac" ),
                ( TITLE_TIME, "jen-elephanto.flac" ),
                ( TITLE_TIME + 1.4, "la-elephanto-havas-balonon.flac" ),
                ( BALLOON_DISAPPEAR_TIME + 1.5, "ho-la-balono-malaperis.flac" ),
                ( BALLOON_DISAPPEAR_TIME + 0.5 + 4.5,
                  "kie-estas-la-balono.flac" ),
                ( 14, "ĉu-ĝi-estas-malantaŭ-la-rinocero.flac" ),
                ( 17, "ne-1.flac" ),
                ( ALLIGATOR_ROTATE_TIME[0],
                  "ĉu-ĝi-estas-en-la-buŝo-de-la-aligatoro.flac" ),
                ( sum(ALLIGATOR_ROTATE_TIME), "ne-2.flac" ),
                ( 32, "ho-la-simio-havas-ĝin-en-la-arbo.flac" ),
                ( BALLOON_PASSOVER_TIME[0], "li-redonas-ĝin.flac" ),
                ( 38, "ili-ĉiuj-trinkas-limonadon.flac" ),
                ( sum(ENTRY_TIME) + 2, "fino.flac" ) ]

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

def credit_layer_name(credit_num):
    if credit_num >= 3:
        credit_num += 1
    return "#layer{}".format(credit_num + 1)

def get_sound_length(sound_file):
    return float(subprocess.check_output(["soxi", "-D", sound_file]))

def format_subtitle_time(timestamp):
    return ("{:02d}:{:02d}:{:02d},{:03d}"
            .format(int(timestamp / 360),
                    int(timestamp / 60) % 60,
                    int(timestamp) % 60,
                    int(timestamp * 1000) % 1000))

if len(sys.argv) == 2 and sys.argv[1] == '-p':
    play_video = True
elif len(sys.argv) == 1:
    play_video = False
else:
    sys.stderr.write("usage: {} [-p]\n".format(sys.argv[0]))
    sys.exit(1)

if not play_video:
    args = ["sox"]
    args.extend(map(lambda x: x[1], AUDIO_TIMES))
    args.extend(["audio.flac", "pad"])

    current_pos = 0.0
    for i in range(len(AUDIO_TIMES) - 1):
        sound_length = get_sound_length(AUDIO_TIMES[i][1])
        current_pos += sound_length
        args.append("{}@{}".format(AUDIO_TIMES[i + 1][0] -
                                   AUDIO_TIMES[i][0] - sound_length,
                                   current_pos))

    subprocess.check_call(args)

    subprocess.check_call(["ffmpeg",
                           "-i", "021914bgm2(happytune).mp3",
                           "-ar", "44100",
                           "-y",
                           "music.flac"])

    subprocess.check_call(["sox",
                           "--combine", "mix",
                           "-v", "0.3",
                           "music.flac", "audio.flac", "soundtrack.flac",
                           "norm"])

with open("rough-subtitles.srt", mode="w", encoding="utf-8") as srt_out:
    i = 1
    for audio in AUDIO_TIMES:
        sound_end = audio[0] + get_sound_length(audio[1])
        srt_out.write("{}\n"
                      "{} --> {}\n"
                      "{}\n"
                      "\n".format(i,
                                  format_subtitle_time(audio[0]),
                                  format_subtitle_time(sound_end),
                                  audio[1]))
        i += 1

elephant_svg = Rsvg.Handle.new_from_file('elephant.svg')
credits_svg = Rsvg.Handle.new_from_file('credits.svg')

title_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                   WIDTH // SCALE,
                                   HEIGHT // SCALE)
cr = cairo.Context(title_surface)
cr.scale(1.0 / SCALE, 1.0 / SCALE)
cr.save()
cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
cr.set_operator(cairo.OPERATOR_SOURCE)
cr.paint()
cr.restore()
render_sub(elephant_svg, cr, "#layer10")

title_pattern = cairo.SurfacePattern(title_surface)

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

n_main_frames = (sum(ENTRY_TIME) + 2) * FRAME_RATE

for frame_num in range(n_main_frames):
    elapsed_time = frame_num / FRAME_RATE

    camera_time = elapsed_time
    in_pause = False

    for pause in PAUSES:
        if elapsed_time >= pause[0]:
            if elapsed_time >= pause[0] + pause[1]:
                camera_time -= pause[1]
            else:
                in_pause = True
                camera_time -= elapsed_time - pause[0]
                break

    camera_pos = camera_time * 300

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

    monkey_angle = rotation_sin * MONKEY_ROTATION

    cr.save()
    cr.translate(MONKEY_POS - camera_pos, 0.0)
    # monkey tree
    render_sub(elephant_svg, cr, "#layer16")
    # monkey body
    cr.save()
    rotate_about(cr,
                 *MONKEY_HAND_POINT,
                 angle = monkey_angle)
    render_sub(elephant_svg, cr, "#layer14")
    cr.restore()
    # monkey hand
    render_sub(elephant_svg, cr, "#layer15")
    cr.restore()

    cr.save()
    if elapsed_time >= ENTRY_TIME[0]:
        if elapsed_time >= ENTRY_TIME[0] + ENTRY_TIME[1]:
            rhino_pos = RHINO_ENTRY_END
        else:
            rhino_pos = ((elapsed_time - ENTRY_TIME[0]) *
                         (RHINO_ENTRY_END - RHINO_ENTRY_START) /
                         ENTRY_TIME[1] +
                         RHINO_ENTRY_START)
    else:
        rhino_pos = RHINO_POS - camera_pos
    cr.translate(rhino_pos, 0.0)
    cr.save()
    rotate_about(cr,
                 *RHINO_TAIL_POINT,
                 angle = RHINO_TAIL_ROTATION * rotation_sin)
    render_sub(elephant_svg, cr, "#layer9")
    cr.restore()
    render_sub(elephant_svg, cr, "#layer8")
    cr.restore()

    cr.save()
    if elapsed_time >= ENTRY_TIME[0]:
        if elapsed_time >= ENTRY_TIME[0] + ENTRY_TIME[1]:
            alligator_pos = 0
        else:
            alligator_pos = ((ENTRY_TIME[0] + ENTRY_TIME[1] - elapsed_time) *
                             ALLIGATOR_ENTRY_START /
                             ENTRY_TIME[1])
    else:
        alligator_pos = ALLIGATOR_POS - camera_pos
    cr.translate(alligator_pos, 0.0)
    # bodge to cover up the join on the alligator head
    render_sub(elephant_svg, cr, "#layer13")
    # alligator head
    cr.save()
    if (elapsed_time >= ALLIGATOR_ROTATE_TIME[0] and
        elapsed_time < ALLIGATOR_ROTATE_TIME[1] + ALLIGATOR_ROTATE_TIME[0]):
        angle = math.sin((elapsed_time - ALLIGATOR_ROTATE_TIME[0]) * math.pi /
                         ALLIGATOR_ROTATE_TIME[1]) * ALLIGATOR_ROTATION
        rotate_about(cr,
                     *ALLIGATOR_HEAD_POINT,
                     angle = angle)
    render_sub(elephant_svg, cr, "#layer12")
    cr.restore()
    # alligator body
    render_sub(elephant_svg, cr, "#layer11")
    cr.restore()

    if elapsed_time >= ENTRY_TIME[0]:
        cr.save()
        cr.translate(alligator_pos, 0.0)
        render_sub(elephant_svg, cr, "#layer17")
        cr.restore()

    if in_pause:
        rotation_angle = 0
        rotation_sin = 0
    else:
        rotation_angle = HEAD_ROTATION * rotation_sin

    feet_frame_num = min(len(ELEPHANT_FRAMES) - 1,
                         max(int((rotation_sin / 2.0 + 0.5) *
                                 (len(ELEPHANT_FRAMES) - 1) + 0.5), 0))

    render_sub(elephant_svg, cr, "#" + ELEPHANT_FRAMES[feet_frame_num])

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
    elif elapsed_time >= BALLOON_PASSOVER_TIME[0]:
        target = (BALLOON_NOSE_POINT[0], HEIGHT - 1 - BALLOON_NOSE_POINT[1])
        if elapsed_time >= BALLOON_PASSOVER_TIME[0] + BALLOON_PASSOVER_TIME[1]:
            balloon_pos = target
        else:
            fraction = ((elapsed_time - BALLOON_PASSOVER_TIME[0]) /
                    BALLOON_PASSOVER_TIME[1])
            fraction = math.sin(fraction * math.pi / 2.0)

            balloon_pos = ((target[0] - balloon_base[0]) *
                           fraction + balloon_base[0],
                           (target[1] - balloon_base[1]) *
                           fraction + balloon_base[1])
    elif camera_pos >= ALLIGATOR_POS:
        hold_point = rotate_point(-monkey_angle,
                                  MONKEY_HOLD_POINT[0] - MONKEY_HAND_POINT[0],
                                  MONKEY_HOLD_POINT[1] - MONKEY_HAND_POINT[1])
        balloon_pos = (MONKEY_HAND_POINT[0] + MONKEY_POS -
                       camera_pos + hold_point[0],
                       HEIGHT - 1 - (MONKEY_HAND_POINT[1] + hold_point[1]))
        balloon_base = (balloon_pos[0], balloon_pos[1])
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

    if elapsed_time < TITLE_TIME + TITLE_FADE_TIME:
        cr.save()
        identity_matrix = cairo.Matrix()
        cr.set_matrix(identity_matrix)
        cr.set_source(title_pattern)
        if elapsed_time >= TITLE_TIME:
            cr.paint_with_alpha(1.0 - (elapsed_time - TITLE_TIME) /
                                TITLE_FADE_TIME)
        else:
            cr.paint()
        cr.restore()

    write_frame(ffout, surface)

    if frame_num == 0:
        surface.write_to_png('title.png')

n_credit_frames = ((CREDIT_TIME * N_CREDITS +
                    CREDIT_SLIDE_TIME * (N_CREDITS - 1)) *
                   FRAME_RATE)

for frame_num in range(n_credit_frames):
    elapsed_time = frame_num / FRAME_RATE
    credit_num = int(elapsed_time / (CREDIT_TIME + CREDIT_SLIDE_TIME))
    in_credit_time = elapsed_time % (CREDIT_TIME + CREDIT_SLIDE_TIME)

    cr.set_source_rgb(170 / 255, 170 / 255, 255 / 255)
    cr.paint()
    
    if in_credit_time < CREDIT_TIME:
        render_sub(credits_svg, cr, credit_layer_name(credit_num))
    else:
        slide_fraction = (-math.cos((in_credit_time - CREDIT_TIME) *
                                    math.pi / CREDIT_SLIDE_TIME) /
                          2.0 + 0.5)
        cr.save()
        cr.translate(0.0, -slide_fraction * HEIGHT)
        render_sub(credits_svg, cr, credit_layer_name(credit_num))
        cr.translate(0.0, HEIGHT)
        render_sub(credits_svg, cr, credit_layer_name(credit_num + 1))
        cr.restore()
        
    write_frame(ffout, surface)

# Pad out to exactly the length of the music
for i in range(n_credit_frames + n_main_frames, int(63.31 * FRAME_RATE)):
    write_frame(ffout, surface)

ffout.stdin.close()

if ffout.wait() != 0:
    raise Exception("convert failed")

if not play_video:
    ret = subprocess.call(["ffmpeg",
                           "-i", "elephant-no-sound.webm",
                           "-i", "soundtrack.flac",
                           "-shortest",
                           "-c:v", "copy",
                           "-c:a", "libvorbis",
                           "-aq", "4",
                           "-y",
                           "elephant.webm"])
    if ret != 0:
        raise Exception("ffmpeg failed")
