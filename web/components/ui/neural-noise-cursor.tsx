"use client";

import React, { useEffect, useRef } from "react";

type NeuralNoiseProps = {
  /** Canvas opacity (0..1) */
  opacity?: number;
  /** Pointer attraction strength (0..2) — scales pointer distance term */
  pointerStrength?: number;
  /** Time scale multiplier (0.25..4) */
  timeScale?: number;
  /** Class to override wrapper layout; defaults to full-bleed vertical sections */
  className?: string;
};

function NeuralNoise({
  opacity = 0.95,
  pointerStrength = 1,
  timeScale = 1,
  className = "relative min-h-[300vh] bg-[#151912] overflow-x-hidden",
}: NeuralNoiseProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const uniformsRef = useRef<Record<string, WebGLUniformLocation | null>>({});
  const rafRef = useRef<number>(0);

  const pointer = useRef({ x: 0, y: 0, tx: 0, ty: 0 });
  const scrollProgress = useRef(0);
  const startTS = useRef<number>(0);

  // Vertex & Fragment shaders (ported from your markup)
  const VERT = `
    precision mediump float;
    attribute vec2 a_position;
    varying vec2 vUv;
    void main() {
      vUv = 0.5 * (a_position + 1.0);
      gl_Position = vec4(a_position, 0.0, 1.0);
    }
  `;

  const FRAG = `
    precision mediump float;
    varying vec2 vUv;
    uniform float u_time;
    uniform float u_ratio;
    uniform vec2  u_pointer_position;
    uniform float u_scroll_progress;
    uniform float u_pointer_strength;
    uniform float u_time_scale;

    vec2 rotate(vec2 uv, float th) {
      return mat2(cos(th), sin(th), -sin(th), cos(th)) * uv;
    }

    float neuro_shape(vec2 uv, float t, float p) {
      vec2 sine_acc = vec2(0.0);
      vec2 res = vec2(0.0);
      float scale = 8.0;

      for (int j = 0; j < 15; j++) {
        uv = rotate(uv, 1.0);
        sine_acc = rotate(sine_acc, 1.0);
        vec2 layer = uv * scale + float(j) + sine_acc - t;
        sine_acc += sin(layer) + 2.4 * p;
        res += (0.5 + 0.5 * cos(layer)) / scale;
        scale *= 1.2;
      }
      return res.x + res.y;
    }

    void main() {
      vec2 uv = 0.5 * vUv;
      uv.x *= u_ratio;

      // pointer falloff
      vec2 pointer = vUv - u_pointer_position;
      pointer.x *= u_ratio;
      float p = clamp(length(pointer), 0.0, 1.0);
      p = 0.5 * pow(1.0 - p, 2.0) * u_pointer_strength;

      float t = 0.001 * u_time * u_time_scale;

      float noise = neuro_shape(uv, t, p);
      noise = 1.2 * pow(noise, 3.0);
      noise += pow(noise, 10.0);
      noise = max(0.0, noise - 0.5);
      noise *= (1.0 - length(vUv - 0.5));

      // Animated palette by scroll
      vec3 base = normalize(vec3(
        0.2,
        0.5 + 0.4 * cos(3.0 * u_scroll_progress),
        0.5 + 0.5 * sin(3.0 * u_scroll_progress)
      ));

      vec3 color = base * noise;
      gl_FragColor = vec4(color, noise);
    }
  `;

  useEffect(() => {
    const canvas = canvasRef.current!;
    const gl =
      (canvas.getContext("webgl") ||
        canvas.getContext("experimental-webgl")) as WebGLRenderingContext | null;

    if (!gl) {
      canvas.style.display = "none";
      return;
    }

    glRef.current = gl;

    const compile = (src: string, type: number) => {
      const sh = gl.createShader(type)!;
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(sh));
        gl.deleteShader(sh);
        return null;
      }
      return sh;
    };

    const vs = compile(VERT, gl.VERTEX_SHADER);
    const fs = compile(FRAG, gl.FRAGMENT_SHADER);
    if (!vs || !fs) return;

    const program = gl.createProgram()!;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error(gl.getProgramInfoLog(program));
      return;
    }
    gl.useProgram(program);

    // Quad buffer
    const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
    const vbo = gl.createBuffer()!;
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    // a_position
    const aPos = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    // uniforms
    const getU = (name: string) => gl.getUniformLocation(program, name);
    const uniforms = {
      u_time: getU("u_time"),
      u_ratio: getU("u_ratio"),
      u_pointer_position: getU("u_pointer_position"),
      u_scroll_progress: getU("u_scroll_progress"),
      u_pointer_strength: getU("u_pointer_strength"),
      u_time_scale: getU("u_time_scale"),
    };
    uniformsRef.current = uniforms;

    // initial static uniforms
    gl.uniform1f(uniforms.u_pointer_strength, pointerStrength);
    gl.uniform1f(uniforms.u_time_scale, timeScale);

    // sizing
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = Math.floor(window.innerWidth * dpr);
      const h = Math.floor(window.innerHeight * dpr);
      canvas.width = w;
      canvas.height = h;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      gl.viewport(0, 0, w, h);
      gl.uniform1f(uniforms.u_ratio, w / h);
    };

    // pointer & scroll
    const updatePointer = (x: number, y: number) => {
      pointer.current.tx = x;
      pointer.current.ty = y;
    };

    const onPointerMove = (e: PointerEvent) => updatePointer(e.clientX, e.clientY);
    const onTouchMove = (e: TouchEvent) => {
      if (e.targetTouches?.[0]) {
        updatePointer(e.targetTouches[0].clientX, e.targetTouches[0].clientY);
      }
    };
    const onClick = (e: MouseEvent) => updatePointer(e.clientX, e.clientY);

    const onScroll = () => {
      scrollProgress.current = window.pageYOffset / (2 * window.innerHeight);
    };

    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("touchmove", onTouchMove, { passive: true });
    window.addEventListener("click", onClick);
    window.addEventListener("scroll", onScroll, { passive: true });

    resize();
    onScroll();

    // animation loop
    startTS.current = performance.now();
    const loop = (now: number) => {
      rafRef.current = requestAnimationFrame(loop);

      // smooth pointer
      const p = pointer.current;
      p.x += (p.tx - p.x) * 0.2;
      p.y += (p.ty - p.y) * 0.2;

      // uniforms per frame
      gl.uniform1f(uniforms.u_time, now - startTS.current);
      gl.uniform2f(
        uniforms.u_pointer_position,
        p.x / window.innerWidth,
        1 - p.y / window.innerHeight
      );
      gl.uniform1f(uniforms.u_scroll_progress, scrollProgress.current);

      // draw
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("touchmove", onTouchMove);
      window.removeEventListener("click", onClick);
      window.removeEventListener("scroll", onScroll);
      // cleanup GL resources
      gl.deleteBuffer(vbo);
      gl.deleteProgram(program);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pointerStrength, timeScale]);

  return (
    <section className={className}>
      {/* Shader Canvas */}
      <canvas
        ref={canvasRef}
        className="pointer-events-none fixed inset-0 w-full h-full"
        style={{ opacity }}
      />

      {/* Content */}
      <div className="relative z-[1] w-full min-h-screen flex items-center justify-center font-sans text-white pointer-events-none">
        <div className="text-center pointer-events-auto flex flex-col items-center">
          <h1 className="text-6xl md:text-8xl font-black mb-4 tracking-tighter">CGPA MONITOR</h1>
          <p className="text-xl md:text-2xl font-light text-white/80 mb-8 max-w-2xl text-center">
            Track your SGPA/CGPA with back-paper handling.
          </p>
          <a href="/leaderboard" className="bg-white text-black px-8 py-4 rounded-full font-bold text-lg hover:scale-105 transition-transform duration-300">
            View Leaderboard
          </a>
        </div>
      </div>
    </section>
  );
}

export { NeuralNoise };
