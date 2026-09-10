# 7. Shader Modules

[← Back to index](README.md) · Previous: [Swap Chain & Image Views](06-swapchain.md) · Next: [Graphics Pipeline →](08-pipeline.md)

Vulkan doesn't compile GLSL itself — shaders have to already be compiled to **SPIR-V** bytecode before Vulkan ever sees them. This chapter writes the simplest possible shader pair and loads the compiled result.

## The shaders

For a first triangle, there's no need for a vertex buffer or a uniform buffer at all — the three positions and colors can just be hardcoded in the shader and indexed by `gl_VertexIndex`, the built-in that tells the shader which of the 3 vertices in this draw call it's currently processing:

`hello_triangle.vert`:
```glsl
#version 450 core

vec2 positions[3] = vec2[](
    vec2(0.0, -0.5),
    vec2(0.5, 0.5),
    vec2(-0.5, 0.5)
);

vec3 colors[3] = vec3[](
    vec3(1.0, 0.0, 0.0),
    vec3(0.0, 1.0, 0.0),
    vec3(0.0, 0.0, 1.0)
);

layout(location = 0) out vec3 fragColor;

void main() {
    gl_Position = vec4(positions[gl_VertexIndex], 0.0, 1.0);
    fragColor = colors[gl_VertexIndex];
}
```

`hello_triangle.frag`:
```glsl
#version 450 core

layout(location = 0) in vec3 fragColor;

layout(location = 0) out vec4 outColor;

void main() {
    outColor = vec4(fragColor, 1.0);
}
```

`fragColor` is interpolated automatically across the triangle's surface between the vertex and fragment stage — that's why the triangle ends up with a smooth color gradient instead of three flat-colored thirds.

> This is deliberately the simplest shader that can exist — no vertex buffer, no descriptor sets, no camera transform. Part 2 replaces both files with versions that read real vertex attributes and a UBO.

## Compiling to SPIR-V

The Vulkan SDK ships `glslc` for exactly this. Run it once per shader, and put the output in a `shaders/` folder next to your script (that's where `load_shader()` below expects to find them):

```bash
glslc hello_triangle.vert -o shaders/hello_triangle.vert.spv
glslc hello_triangle.frag -o shaders/hello_triangle.frag.spv
```

Re-run this any time you edit the `.vert`/`.frag` source — Vulkan only ever sees the `.spv` output, so a stale `.spv` file silently keeps the old shader running.

## Loading a shader module

```python
def load_shader(self, shader_file):
    with open(shader_file, "rb") as f:
        code = f.read()
    word_count = len(code) // 4
    buf = (c_uint32 * word_count).from_buffer_copy(code)
    create_info = VkShaderModuleCreateInfo(codeSize=len(code), pCode=cast(buf, POINTER(c_uint32)))
    module = VkShaderModule()
    check(self.device.vkCreateShaderModule(create_info, None, byref(module)), f'Failed to load "{shader_file}" shader module')
    return module, buf
```

SPIR-V is a stream of 32-bit words, so the raw bytes read from disk get reinterpreted as a `c_uint32` array (`word_count = len(code) // 4`) rather than passed as a plain byte buffer — that's what `pCode` actually expects. `buf` is returned alongside `module` mainly to keep it referenced for the duration of the call; once `vkCreateShaderModule` returns, the driver has its own copy and `module` is the only handle you'll use going forward.

Call it once per shader:

```python
vert_module, vert_buf = self.load_shader("shaders/hello_triangle.vert.spv")
frag_module, frag_buf = self.load_shader("shaders/hello_triangle.frag.spv")
```

These two modules feed directly into the pipeline's shader stages in the next chapter.

[← Back to index](README.md) · Previous: [Swap Chain & Image Views](06-swapchain.md) · Next: [Graphics Pipeline →](08-pipeline.md)