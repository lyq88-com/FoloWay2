# -*- coding: utf-8 -*-
"""
生成正念模块 12 条环境音床（30 秒无缝循环 WAV）。

替换旧版「低频正弦嗡鸣 + 一阶低通噪声」音床——旧版听起来像持续的呼吸声/嗡嗡声，
所以整体换成 Calm / 潮汐 / 小睡眠这类 App 上最常用的助眠声音：
轻雨、雨落叶、海浪、溪流、森林、篝火、棕噪音、颂钵音垫。

无缝循环原理（保证 buf[N-1] -> buf[0] 无爆音）：
  1. 噪声层用长度 N 的 irfft 频域成形，得到的信号在 N 点上严格周期；
  2. 包络用周期整除 30 秒的余弦，或同样由 irfft 生成的低频 LFO；
  3. 雨滴 / 爆裂 / 鸟鸣 / 颂钵等瞬态事件按 (start + i) % N 环绕叠加。
  因此不需要交叉淡化，循环点天然连续。

输出：server/uploads/audio/*.wav（由 FastAPI 的 /uploads 静态挂载提供）
"""
import os
import wave

import numpy as np

SR = 22050                 # 采样率（环境音床足够，文件更小）
LOOP_SEC = 30              # 循环长度（秒）
N = SR * LOOP_SEC          # 单圈采样数
TARGET_RMS_DB = -20.0      # 目标响度（比旧版安静很多，垫在引导语下面刚好）
PEAK_MAX = 0.85            # 峰值上限，防止削波
SEED = 20261111

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "server", "uploads", "audio")


# ============ 基础工具 ============
def make_rng(tag):
    return np.random.default_rng(SEED + tag)


def shaped(rng, slope, lo=None, hi=None):
    """频域成形噪声：slope=0 白噪声 / 1 粉红 / 2 棕噪声；返回单位 RMS。"""
    w = rng.standard_normal(N)
    spec = np.fft.rfft(w)
    f = np.fft.rfftfreq(N, 1.0 / SR)
    f[0] = f[1]
    amp = f ** (-slope / 2.0)
    if lo:
        amp = amp / (1.0 + (lo / f) ** 6)
    if hi:
        amp = amp / (1.0 + (f / hi) ** 6)
    x = np.fft.irfft(spec * amp, N)
    return x / (float(np.sqrt(np.mean(x * x))) + 1e-12)


def lfo(rng, lo=0.2, hi=2.0, power=1.0):
    """0~1 的慢速随机起伏（仍然严格 30 秒周期）。"""
    x = shaped(rng, 0.5, lo, hi)
    x = x / (float(np.max(np.abs(x))) + 1e-12)
    return (0.5 + 0.5 * x) ** power


def periodic(period_sec, power=1.0, phase=0.0):
    """周期必须整除 30 秒，保证循环点连续。"""
    t = np.arange(N) / SR
    e = 0.5 - 0.5 * np.cos(2.0 * np.pi * t / period_sec + phase)
    return e if power == 1.0 else e ** power


def add_event(buf, sig, start, amp):
    """把瞬态事件环绕写入缓冲区，跨循环点也不会断。"""
    idx = (int(start) + np.arange(sig.size)) % N
    np.add.at(buf, idx, sig * amp)


def burst(rng, dur, lo, hi, attack=0.002, tau=None):
    """带通噪声脉冲：雨滴 / 水泡 / 柴火爆裂。"""
    L = max(16, int(dur * SR))
    w = rng.standard_normal(L)
    spec = np.fft.rfft(w)
    f = np.fft.rfftfreq(L, 1.0 / SR)
    f[0] = f[1]
    amp = 1.0 / (1.0 + (lo / f) ** 4) / (1.0 + (f / hi) ** 4)
    y = np.fft.irfft(spec * amp, L)
    t = np.arange(L) / SR
    env = (1.0 - np.exp(-t / max(attack, 1e-4))) * np.exp(-t / (tau or dur * 0.3))
    fade = max(8, int(0.005 * SR))
    env[-fade:] *= np.linspace(1.0, 0.0, fade)
    y *= env
    return y / (float(np.max(np.abs(y))) + 1e-12)


def chirp(rng, f0, f1, dur):
    """鸟鸣：短促上滑音。"""
    L = int(dur * SR)
    t = np.arange(L) / SR
    ph = 2.0 * np.pi * np.cumsum(f0 + (f1 - f0) * (t / dur)) / SR
    env = (1.0 - np.exp(-t / 0.004)) * np.exp(-t / (dur * 0.45))
    fade = max(8, int(0.004 * SR))
    env[-fade:] *= np.linspace(1.0, 0.0, fade)
    return np.sin(ph) * env / (float(np.max(np.abs(np.sin(ph) * env))) + 1e-12)


def bell(rng, base, dur=5.0):
    """颂钵：基频 + 非谐泛音，慢衰减。"""
    L = int(dur * SR)
    t = np.arange(L) / SR
    y = np.zeros(L)
    for ratio, amp, k in ((1.0, 1.0, 1.0), (2.0, 0.45, 1.5),
                          (2.76, 0.24, 2.2), (5.4, 0.10, 3.4), (8.2, 0.04, 5.0)):
        ph = rng.random() * 2.0 * np.pi
        y += amp * np.sin(2.0 * np.pi * base * ratio * t + ph) * np.exp(-t * k / (dur * 0.32))
    y *= 1.0 - np.exp(-t / 0.012)
    fade = max(8, int(0.02 * SR))
    y[-fade:] *= np.linspace(1.0, 0.0, fade)
    return y / (float(np.max(np.abs(y))) + 1e-12)


def quantize(freq):
    """把频率对齐到 1/30 Hz 的整数倍，纯正弦也能 30 秒整周期循环。"""
    return round(freq * LOOP_SEC) / LOOP_SEC


# ============ 各类音床 ============
def track_rain(rng, density=16, brightness=1.0):
    """轻柔雨声：高频嘶声 + 低频雨幕 + 稀疏雨滴。"""
    base = shaped(rng, 0.55, 380, 7200)
    body = shaped(rng, 1.5, 40, 320)
    n = base + body * 0.10
    n *= 0.94 + 0.06 * lfo(rng, 0.06, 0.35)          # 极轻的疏密变化，不像呼吸
    for _ in range(int(LOOP_SEC * density)):
        start = int(rng.integers(0, N))
        amp = 0.06 + 0.26 * float(rng.random()) ** 3
        dur = 0.025 + 0.055 * float(rng.random())
        add_event(n, burst(rng, dur, 1100 * brightness, 5200), start, amp * 0.35)
    return n


def track_rain_leaf(rng):
    """雨打树叶：中频更厚，雨滴更密更软。"""
    base = shaped(rng, 0.7, 300, 5000)
    mid = shaped(rng, 0.9, 700, 2600)
    n = base + mid * 0.35
    n *= 0.95 + 0.05 * lfo(rng, 0.08, 0.4)
    for _ in range(int(LOOP_SEC * 26)):
        add_event(n, burst(rng, 0.05 + 0.06 * float(rng.random()), 600, 3000),
                  int(rng.integers(0, N)), 0.05 + 0.12 * float(rng.random()) ** 2)
    return n


def track_ocean(rng, period=7.5):
    """海浪：低频涌浪 + 高频浪花，浪花略微滞后于浪峰。"""
    body = shaped(rng, 1.2, 45, 460)
    foam = shaped(rng, 0.35, 800, 6500)
    swell = periodic(period, power=1.6)
    foam_env = np.roll(periodic(period, power=1.2), int(0.45 * SR))
    n = body * (0.24 + 0.76 * swell) * 0.8
    n += foam * (0.10 + 0.90 * foam_env) * 0.85
    # 第二层错周期浪，避免机械重复（15 秒整除 30，循环点仍连续）
    n += body * 0.18 * periodic(15.0, power=2.0, phase=1.1)
    return n


def track_stream(rng, deep=False):
    """溪流：宽带水声 + 快速涌动 + 咕咚水泡。"""
    base = shaped(rng, 0.15, 500 if deep else 650, 6500 if deep else 7600)
    churn = 0.52 + 0.48 * lfo(rng, 1.5, 6.0)
    low = shaped(rng, 1.3, 60, 520)
    n = base * (0.55 + 0.45 * churn) + low * 0.18
    for _ in range(int(LOOP_SEC * 8)):
        add_event(n, burst(rng, 0.02 + 0.03 * float(rng.random()), 450, 1800),
                  int(rng.integers(0, N)), 0.10 * float(rng.random()))
    return n


def track_forest(rng):
    """森林：风吹树叶 + 远处林中低频 + 稀疏鸟鸣。"""
    wind = shaped(rng, 0.7, 150, 3500)
    gust = lfo(rng, 0.07, 0.5)
    low = shaped(rng, 1.5, 40, 400)
    n = wind * (0.32 + 0.68 * gust) + low * (0.45 + 0.55 * gust) * 0.25
    for _ in range(7):
        start = int(rng.integers(0, N))
        f0 = float(rng.uniform(2100, 3100))
        for j in range(int(rng.integers(2, 4))):
            add_event(n, chirp(rng, f0, f0 * float(rng.uniform(1.15, 1.45)), 0.07 + 0.05 * float(rng.random())),
                      start + j * int(0.11 * SR), 0.10)
    return n


def track_fire(rng):
    """篝火：低频燃烧 + 细碎嘶声 + 爆裂声。"""
    rumble = shaped(rng, 1.6, 40, 420)
    flick = lfo(rng, 1.0, 3.2)
    hiss = shaped(rng, 0.4, 700, 5200)
    n = rumble * (0.5 + 0.5 * flick) * 0.85 + hiss * (0.35 + 0.65 * flick) * 0.22
    for _ in range(int(LOOP_SEC * 14)):
        add_event(n, burst(rng, 0.006 + 0.02 * float(rng.random()), 1400, 6500,
                           attack=0.0005, tau=0.012),
                  int(rng.integers(0, N)), 0.30 * float(rng.random()) ** 1.5)
    return n


def track_brown(rng, with_pad=False):
    """棕噪音：低频柔和、无高频刺激，起伏极小（避免呼吸感）。"""
    n = shaped(rng, 1.7, 25, 2600)
    n += shaped(rng, 1.0, 300, 3000) * 0.22      # 补一点中频，手机外放也不至于发闷
    n *= 0.97 + 0.03 * lfo(rng, 0.05, 0.3)
    if with_pad:
        n = n * 0.78 + track_pad(rng) * 0.22
    return n


def track_pad(rng):
    """柔和音垫：两组合弦每 15 秒缓慢交替 + 极轻气声 + 颂钵点缀。

    只用一组和弦会变成持续的「嗡嗡」声，这里让 C 大调与 A 小调互相淡入淡出，
    形成类似市面冥想音乐的和声流动感。
    """
    t = np.arange(N) / SR
    n = np.zeros(N)
    chord_a = ((261.63, 0.24), (329.63, 0.18), (392.00, 0.15))
    chord_b = ((220.00, 0.22), (261.63, 0.18), (329.63, 0.15))
    mix = 0.5 + 0.5 * np.cos(2.0 * np.pi * t / 15.0)     # 15 秒整除 30，循环点连续
    for chord, gain in ((chord_a, mix), (chord_b, 1.0 - mix)):
        for f, a in chord:
            fq = quantize(f + float(rng.uniform(-0.10, 0.10)))
            ph = rng.random() * 2.0 * np.pi
            vib = 1.0 + 0.0012 * np.sin(2.0 * np.pi * t / 7.5 + ph)
            n += gain * a * np.sin(2.0 * np.pi * fq * t + ph) * vib
    n += np.sin(2.0 * np.pi * quantize(130.81) * t) * 0.08   # 低八度垫底
    n += shaped(rng, 1.2, 300, 2500) * 0.03
    for k, note in enumerate((523.25, 659.25, 523.25, 392.00)):
        add_event(n, bell(rng, quantize(note)), int(k * 7.5 * SR), 0.20)
    return n


# ============ 音床清单 ============
TRACKS = {
    "breath_5min":   lambda: track_rain(make_rng(1)),
    "breath_10min":  lambda: track_ocean(make_rng(2), 7.5),
    "breath_15min":  lambda: track_stream(make_rng(3)),
    "scan_5min":     lambda: track_forest(make_rng(4)),
    "scan_10min":    lambda: track_rain_leaf(make_rng(5)),
    "scan_20min":    lambda: track_stream(make_rng(6), deep=True),
    "med_5min":      lambda: track_pad(make_rng(7)),
    "med_15min":     lambda: track_ocean(make_rng(8), 10.0),
    "med_30min":     lambda: track_brown(make_rng(9)),
    "anxiety_5min":  lambda: track_fire(make_rng(10)),
    "anxiety_15min": lambda: track_rain(make_rng(11), density=12, brightness=0.9),
    "anxiety_25min": lambda: track_brown(make_rng(12), with_pad=True),
}


def normalize(x):
    rms = float(np.sqrt(np.mean(x * x))) + 1e-12
    x = x * (10.0 ** (TARGET_RMS_DB / 20.0) / rms)
    peak = float(np.max(np.abs(x)))
    if peak > PEAK_MAX:
        x = x * (PEAK_MAX / peak)
    return x


def write_wav(path, x):
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    total = 0
    for name, build in TRACKS.items():
        buf = normalize(build())
        path = os.path.join(OUT_DIR, name + ".wav")
        write_wav(path, buf)
        rms_db = 20.0 * np.log10(float(np.sqrt(np.mean(buf * buf))) + 1e-12)
        peak = float(np.max(np.abs(buf)))
        size = os.path.getsize(path)
        total += size
        print("%-14s rms %.1f dBFS  peak %.2f  %5.2f MB" % (name, rms_db, peak, size / 1024 / 1024))
    print("共 %d 个文件，合计 %.2f MB" % (len(TRACKS), total / 1024 / 1024))


if __name__ == "__main__":
    main()
