# -*- coding: utf-8 -*-
"""
Python 星空 / 螺旋星系粒子动画
复刻自抖音「可乐鸡翅^O^」的 Python 星空教程效果
依赖: pip install moderngl glfw numpy
运行: python3 starfield.py
"""

import math
import sys

import glfw
import moderngl
import numpy as np

# ============ 可调参数（对应原视频里的那一组） ============
SHIFT = 20
PRES = 8
PA, PB, PC = 1.0, 0.4, 0.25
CYCLE = 14.0
W, H = 900, 900
WAMP = 3.5      # 波浪振幅
WFREQ = 1.4     # 波浪频率
SWR = 6.0       # 散射 / 扭曲
SPIN = 1.5      # 旋转速度
# =========================================================

N_GALAXY = 26000   # 星系粒子数
N_BRIGHT = 90      # 点缀的亮星数（带十字光芒）


def build_particles():
    """生成螺旋星系粒子：3 条旋臂，中心密、外围薄。"""
    n = N_GALAXY
    # 半径：幂分布，让中心更密
    r = np.random.power(0.45, n) * 4.2
    # 3 条旋臂
    arm = np.random.randint(0, 3, n)
    base_angle = arm * (2.0 * math.pi / 3.0)
    # 螺旋扭曲：半径越大，扭转越多
    twist = r * 1.9
    angle = base_angle + twist + np.random.normal(0.0, 0.28, n)
    x = r * np.cos(angle)
    y = r * np.sin(angle)
    # z 方向厚度：中心厚、外围薄
    z = np.random.normal(0.0, 0.35 * np.exp(-r * 0.55), n)
    # 颜色：中心白亮 -> 外围蓝
    t = np.clip(r / 4.2, 0.0, 1.0)
    # 中心偏暖白，外围偏冷蓝
    cr = (1.0 - t) * 1.0 + t * 0.35
    cg = (1.0 - t) * 0.95 + t * 0.55
    cb = (1.0 - t) * 0.85 + t * 1.0
    # 粒子大小：中心略大
    size = (1.0 - t) * 2.2 + t * 1.1 + np.random.uniform(0.0, 0.6, n)
    pos = np.stack([x, y, z], axis=1).astype("f4")
    col = np.stack([cr, cg, cb], axis=1).astype("f4")
    siz = size.astype("f4")
    return pos, col, siz


def build_bright_stars():
    """少量明亮的点缀星（带十字光芒）。"""
    n = N_BRIGHT
    r = np.random.uniform(0.5, 4.5, n)
    a = np.random.uniform(0.0, 2.0 * math.pi, n)
    x = r * np.cos(a)
    y = r * np.sin(a)
    z = np.random.normal(0.0, 0.4, n)
    pos = np.stack([x, y, z], axis=1).astype("f4")
    col = np.ones((n, 3), dtype="f4") * 1.0
    siz = np.random.uniform(6.0, 12.0, n).astype("f4")
    return pos, col, siz


# ---------------- Shader ----------------
VS_GALAXY = """
#version 330
in vec3 in_pos;
in vec3 in_col;
in float in_size;
uniform mat4 u_proj;
uniform float u_time;
uniform float u_spin;
uniform float u_wamp;
uniform float u_wfreq;
uniform float u_swr;
out vec3 v_col;
out float v_glow;

mat4 rotZ(float a) {
    float c = cos(a), s = sin(a);
    return mat4(c, s, 0, 0,  -s, c, 0, 0,  0,0,1,0,  0,0,0,1);
}

void main() {
    vec3 p = in_pos;
    // 整体绕 z 轴旋转
    float ang = u_time * 0.15 * u_spin;
    p = (rotZ(ang) * vec4(p, 1.0)).xyz;
    // 波浪扰动：沿半径方向的起伏
    float w = sin(length(p.xy) * u_wfreq - u_time * 1.2) * u_wamp * 0.08;
    p.z += w;
    // 轻微径向呼吸
    float breathe = 1.0 + 0.03 * sin(u_time * 0.6);
    p.xy *= breathe;
    // 散射扰动：加一点随机相位的摆动
    p.x += sin(u_time * 0.7 + p.y * u_swr * 0.15) * 0.03;
    p.y += cos(u_time * 0.6 + p.x * u_swr * 0.15) * 0.03;
    gl_Position = u_proj * vec4(p, 1.0);
    gl_PointSize = in_size;
    v_col = in_col;
    v_glow = 1.0;
}
"""

FS_GALAXY = """
#version 330
in vec3 v_col;
in float v_glow;
out vec4 frag;
void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    if (d > 0.5) discard;
    // 柔和发光：中心亮，边缘渐隐
    float alpha = smoothstep(0.5, 0.0, d);
    alpha = pow(alpha, 1.6);
    frag = vec4(v_col, alpha * 0.85);
}
"""

VS_STAR = """
#version 330
in vec3 in_pos;
in vec3 in_col;
in float in_size;
uniform mat4 u_proj;
uniform float u_time;
out vec3 v_col;
out float v_size;
void main() {
    gl_Position = u_proj * vec4(in_pos, 1.0);
    float twinkle = 0.85 + 0.15 * sin(u_time * 3.0 + in_pos.x * 5.0);
    gl_PointSize = in_size * twinkle;
    v_col = in_col;
}
"""

FS_STAR = """
#version 330
in vec3 v_col;
out vec4 frag;
void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float d = length(uv);
    if (d > 0.5) discard;
    // 中心亮点
    float core = smoothstep(0.18, 0.0, d);
    // 十字光芒
    float ray_x = smoothstep(0.03, 0.0, abs(uv.x)) * smoothstep(0.5, 0.0, abs(uv.y));
    float ray_y = smoothstep(0.03, 0.0, abs(uv.y)) * smoothstep(0.5, 0.0, abs(uv.x));
    float glow = smoothstep(0.5, 0.0, d) * 0.4;
    float a = clamp(core + ray_x + ray_y + glow, 0.0, 1.0);
    frag = vec4(v_col, a);
}
"""


def main():
    if not glfw.init():
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.SAMPLES, 4)

    window = glfw.create_window(W, H, "Python Starfield - Galaxy", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    ctx = moderngl.create_context()
    ctx.enable(moderngl.PROGRAM_POINT_SIZE)
    ctx.enable(moderngl.BLEND)
    ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE  # 加色混合，发光感

    # 投影矩阵：正交投影，把 [-5,5] 映射到屏幕
    def ortho(l, r, b, t, n, f):
        return np.array([
            [2/(r-l), 0, 0, -(r+l)/(r-l)],
            [0, 2/(t-b), 0, -(t+b)/(t-b)],
            [0, 0, -2/(f-n), -(f+n)/(f-n)],
            [0, 0, 0, 1],
        ], dtype="f4").T

    proj = ortho(-5.2, 5.2, -5.2, 5.2, -5.0, 5.0)

    # 星系粒子
    g_pos, g_col, g_size = build_particles()
    g_data = np.concatenate([
        g_pos, g_col, g_size[:, None]
    ], axis=1).astype("f4")
    g_prog = ctx.program(vertex_shader=VS_GALAXY, fragment_shader=FS_GALAXY)
    g_vbo = ctx.buffer(g_data.tobytes())
    g_vao = ctx.vertex_array(
        g_prog,
        [(g_vbo, "3f 3f 1f", "in_pos", "in_col", "in_size")],
    )

    # 亮星
    s_pos, s_col, s_size = build_bright_stars()
    s_data = np.concatenate([
        s_pos, s_col, s_size[:, None]
    ], axis=1).astype("f4")
    s_prog = ctx.program(vertex_shader=VS_STAR, fragment_shader=FS_STAR)
    s_vbo = ctx.buffer(s_data.tobytes())
    s_vao = ctx.vertex_array(
        s_prog,
        [(s_vbo, "3f 3f 1f", "in_pos", "in_col", "in_size")],
    )

    # 初始背景
    ctx.clear(0.02, 0.02, 0.06, 1.0)

    clock = glfw.get_time
    t0 = clock()

    while not glfw.window_should_close(window):
        t = clock() - t0

        # 半透明清屏：制造拖尾感
        # 用一个全屏矩形画半透明深色，覆盖上一帧
        # 简单做法：直接用低不透明度清屏（moderngl 不支持半透明清屏，用 blend 画个 quad）
        # 这里直接用较淡的清屏，加色混合下效果接近
        ctx.clear(0.02, 0.02, 0.06, 0.08)

        # 星系粒子
        g_prog["u_proj"].write(proj.tobytes())
        g_prog["u_time"].value = t
        g_prog["u_spin"].value = SPIN
        g_prog["u_wamp"].value = WAMP
        g_prog["u_wfreq"].value = WFREQ
        g_prog["u_swr"].value = SWR
        g_vao.render(moderngl.POINTS)

        # 亮星
        s_prog["u_proj"].write(proj.tobytes())
        s_prog["u_time"].value = t
        s_vao.render(moderngl.POINTS)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
