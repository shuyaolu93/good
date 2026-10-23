# -*- coding: utf-8 -*-
"""离屏渲染太空站一帧。"""
import moderngl
import numpy as np
from space_station import build_station, VS, FS, W, H, SPIN, WAMP

ctx = moderngl.create_standalone_context()
ctx.enable(moderngl.PROGRAM_POINT_SIZE)
ctx.enable(moderngl.BLEND)
ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE

fbo = ctx.simple_framebuffer((W, H))
fbo.use()
fbo.clear(0.01, 0.01, 0.03, 1.0)

def ortho(l, r, b, t, n, f):
    return np.array([
        [2/(r-l), 0, 0, -(r+l)/(r-l)],
        [0, 2/(t-b), 0, -(t+b)/(t-b)],
        [0, 0, -2/(f-n), -(f+n)/(f-n)],
        [0, 0, 0, 1],
    ], dtype="f4").T

proj = ortho(-4.5, 4.5, -4.5, 4.5, -5.0, 5.0)

pos, col, size = build_station()
data = np.concatenate([pos, col, size[:, None]], axis=1).astype("f4")
prog = ctx.program(vertex_shader=VS, fragment_shader=FS)
vbo = ctx.buffer(data.tobytes())
vao = ctx.vertex_array(prog, [(vbo, "3f 3f 1f", "in_pos", "in_col", "in_size")])

prog["u_proj"].write(proj.tobytes())
prog["u_time"].value = 2.0
prog["u_spin"].value = SPIN
prog["u_wamp"].value = WAMP
vao.render(moderngl.POINTS)

img = fbo.read()
from PIL import Image
image = Image.frombytes("RGB", (W, H), img).transpose(Image.FLIP_TOP_BOTTOM)
image.save("/tmp/station_test.png")
print("saved /tmp/station_test.png")
