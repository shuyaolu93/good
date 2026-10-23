# -*- coding: utf-8 -*-
"""离屏渲染测试：渲染一帧星系粒子，保存为 png 验证效果。"""
import math
import moderngl
import numpy as np
from starfield import (build_particles, build_bright_stars,
                       VS_GALAXY, FS_GALAXY, VS_STAR, FS_STAR,
                       W, H, SPIN, WAMP, WFREQ)

ctx = moderngl.create_standalone_context()
ctx.enable(moderngl.PROGRAM_POINT_SIZE)
ctx.enable(moderngl.BLEND)
ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE

fbo = ctx.simple_framebuffer((W, H))
fbo.use()
fbo.clear(0.02, 0.02, 0.06, 1.0)

def ortho(l, r, b, t, n, f):
    return np.array([
        [2/(r-l), 0, 0, -(r+l)/(r-l)],
        [0, 2/(t-b), 0, -(t+b)/(t-b)],
        [0, 0, -2/(f-n), -(f+n)/(f-n)],
        [0, 0, 0, 1],
    ], dtype="f4").T

proj = ortho(-5.2, 5.2, -5.2, 5.2, -5.0, 5.0)

# 星系
g_pos, g_col, g_size = build_particles()
g_data = np.concatenate([g_pos, g_col, g_size[:, None]], axis=1).astype("f4")
g_prog = ctx.program(vertex_shader=VS_GALAXY, fragment_shader=FS_GALAXY)
g_vbo = ctx.buffer(g_data.tobytes())
g_vao = ctx.vertex_array(g_prog, [(g_vbo, "3f 3f 1f", "in_pos", "in_col", "in_size")])

g_prog["u_proj"].write(proj.tobytes())
g_prog["u_time"].value = 2.0
g_prog["u_spin"].value = SPIN
g_prog["u_wamp"].value = WAMP
g_prog["u_wfreq"].value = WFREQ
g_prog["u_swr"].value = 6.0
g_vao.render(moderngl.POINTS)

# 亮星
s_pos, s_col, s_size = build_bright_stars()
s_data = np.concatenate([s_pos, s_col, s_size[:, None]], axis=1).astype("f4")
s_prog = ctx.program(vertex_shader=VS_STAR, fragment_shader=FS_STAR)
s_vbo = ctx.buffer(s_data.tobytes())
s_vao = ctx.vertex_array(s_prog, [(s_vbo, "3f 3f 1f", "in_pos", "in_col", "in_size")])
s_prog["u_proj"].write(proj.tobytes())
s_prog["u_time"].value = 2.0
s_vao.render(moderngl.POINTS)

# 保存截图
img = fbo.read()
from PIL import Image
image = Image.frombytes("RGB", (W, H), img)
image = image.transpose(Image.FLIP_TOP_BOTTOM)
image.save("/tmp/galaxy_test.png")
print("saved /tmp/galaxy_test.png")
