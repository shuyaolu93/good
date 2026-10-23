# -*- coding: utf-8 -*-
"""
Python 太空站粒子动画
基于 starfield.py 模板，用 moderngl 粒子渲染空间站结构
依赖: pip install moderngl glfw numpy
运行: python3 space_station.py
"""

import math
import sys

import glfw
import moderngl
import numpy as np

# ============ 可调参数 ============
W, H = 900, 900
SPIN = 0.8          # 整体旋转速度
WAMP = 3.0          # 摆动幅度
RUN_SECONDS = 15    # 自动运行时长
# ==================================

N_BODY = 40000      # 主体粒子数
N_PANEL = 20000     # 太阳能板粒子数
N_LIGHT = 300       # 舱灯粒子数


def build_station():
    """用粒子拼出空间站结构：核心舱 + 环形重力舱 + 太阳能板 + 对接口。"""
    parts_pos = []
    parts_col = []
    parts_size = []

    # ---- 1. 中心核心舱（沿 z 轴的短圆柱）----
    n = 12000
    cz = np.random.uniform(-0.6, 0.6, n)
    cr = np.random.normal(0.18, 0.03, n)
    ca = np.random.uniform(0, 2 * math.pi, n)
    cx = cr * np.cos(ca)
    cy = cr * np.sin(ca)
    parts_pos.append(np.stack([cx, cy, cz], axis=1))
    # 金属银灰色
    parts_col.append(np.tile([0.75, 0.78, 0.82], (n, 1)))
    parts_size.append(np.random.uniform(1.0, 1.8, n))

    # ---- 2. 环形重力舱（绕 z 轴的大圆环）----
    n = 18000
    ring_r = 1.6
    ra = np.random.uniform(0, 2 * math.pi, n)
    # 环有厚度
    rr = ring_r + np.random.normal(0, 0.12, n)
    rz = np.random.normal(0, 0.08, n)
    rx = rr * np.cos(ra)
    ry = rr * np.sin(ra)
    parts_pos.append(np.stack([rx, ry, rz], axis=1))
    # 银灰 + 部分暖色（窗户灯光）
    warm = np.random.random(n) < 0.15
    col = np.tile([0.7, 0.72, 0.76], (n, 1))
    col[warm] = [1.0, 0.85, 0.5]
    parts_col.append(col)
    parts_size.append(np.random.uniform(0.9, 1.6, n))

    # ---- 3. 连接臂（从核心舱到环形舱的四根辐条）----
    n = 8000
    arm_angles = np.array([0, math.pi/2, math.pi, 3*math.pi/2])
    arm_idx = np.random.randint(0, 4, n)
    t = np.random.uniform(0.2, ring_r, n)  # 从核心到环
    aa = arm_angles[arm_idx]
    ax = t * np.cos(aa)
    ay = t * np.sin(aa)
    az = np.random.normal(0, 0.04, n)
    parts_pos.append(np.stack([ax, ay, az], axis=1))
    parts_col.append(np.tile([0.6, 0.62, 0.66], (n, 1)))
    parts_size.append(np.random.uniform(0.8, 1.3, n))

    # ---- 4. 太阳能板（两片大平板，沿 x 轴伸出）----
    n = 20000
    # 左侧板
    side = np.random.choice([-1, 1], n)
    px = side * np.random.uniform(2.0, 3.5, n)
    py = np.random.normal(0, 0.03, n)
    pz = np.random.uniform(-0.9, 0.9, n)
    parts_pos.append(np.stack([px, py, pz], axis=1))
    # 深蓝色太阳能板
    parts_col.append(np.tile([0.2, 0.35, 0.7], (n, 1)))
    parts_size.append(np.random.uniform(0.7, 1.1, n))

    # ---- 5. 对接口（核心舱上下两个小圆柱）----
    n = 2000
    end = np.random.choice([-1, 1], n)
    dz = end * np.random.uniform(0.6, 0.9, n)
    da = np.random.uniform(0, 2 * math.pi, n)
    dr = np.random.normal(0.1, 0.02, n)
    dx = dr * np.cos(da)
    dy = dr * np.sin(da)
    parts_pos.append(np.stack([dx, dy, dz], axis=1))
    parts_col.append(np.tile([0.8, 0.82, 0.85], (n, 1)))
    parts_size.append(np.random.uniform(0.9, 1.4, n))

    # ---- 6. 舱灯（暖白色亮点）----
    n = N_LIGHT
    # 散在环和核心上的亮点
    lr = np.random.uniform(0.2, ring_r, n)
    la = np.random.uniform(0, 2 * math.pi, n)
    lx = lr * np.cos(la)
    ly = lr * np.sin(la)
    lz = np.random.normal(0, 0.1, n)
    parts_pos.append(np.stack([lx, ly, lz], axis=1))
    parts_col.append(np.tile([1.0, 0.9, 0.6], (n, 1)))
    parts_size.append(np.random.uniform(2.5, 4.0, n))

    pos = np.concatenate(parts_pos, axis=0).astype("f4")
    col = np.concatenate(parts_col, axis=0).astype("f4")
    siz = np.concatenate(parts_size, axis=0).astype("f4")
    return pos, col, siz


# ---------------- Shader ----------------
VS = """
#version 330
in vec3 in_pos;
in vec3 in_col;
in float in_size;
uniform mat4 u_proj;
uniform float u_time;
uniform float u_spin;
uniform float u_wamp;
out vec3 v_col;

mat4 rotZ(float a) {
    float c = cos(a), s = sin(a);
    return mat4(c, s, 0, 0,  -s, c, 0, 0,  0,0,1,0,  0,0,0,1);
}
mat4 rotX(float a) {
    float c = cos(a), s = sin(a);
    return mat4(1,0,0,0,  0,c,s,0,  0,-s,c,0,  0,0,0,1);
}

void main() {
    vec3 p = in_pos;
    // 整体绕 z 轴旋转
    float ang = u_time * 0.2 * u_spin;
    p = (rotZ(ang) * vec4(p, 1.0)).xyz;
    // 轻微俯仰摆动
    p = (rotX(sin(u_time * 0.3) * 0.15) * vec4(p, 1.0)).xyz;
    // 整体轻微摆动
    p.y += sin(u_time * 0.5) * u_wamp * 0.05;
    gl_Position = u_proj * vec4(p, 1.0);
    gl_PointSize = in_size;
    v_col = in_col;
}
"""

FS = """
#version 330
in vec3 v_col;
out vec4 frag;
void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    if (d > 0.5) discard;
    float alpha = smoothstep(0.5, 0.0, d);
    alpha = pow(alpha, 1.5);
    frag = vec4(v_col, alpha * 0.9);
}
"""


def main():
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(W, H, "Space Station - Particles", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    ctx = moderngl.create_context()
    ctx.enable(moderngl.PROGRAM_POINT_SIZE)
    ctx.enable(moderngl.BLEND)
    ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE

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
    vao = ctx.vertex_array(
        prog,
        [(vbo, "3f 3f 1f", "in_pos", "in_col", "in_size")],
    )

    ctx.clear(0.01, 0.01, 0.03, 1.0)
    clock = glfw.get_time
    t0 = clock()

    while not glfw.window_should_close(window):
        t = clock() - t0
        if t >= RUN_SECONDS:
            break

        ctx.clear(0.01, 0.01, 0.03, 0.06)

        prog["u_proj"].write(proj.tobytes())
        prog["u_time"].value = t
        prog["u_spin"].value = SPIN
        prog["u_wamp"].value = WAMP
        vao.render(moderngl.POINTS)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
