# 8. Graphics Pipeline (Dynamic Rendering)

[← Back to index](README.md) · Previous: [Shader Modules](07-shader-modules.md) · Next: [Command Pool & Buffers →](09-command-buffers.md)

The pipeline bundles everything about *how* a draw call runs — shaders, how vertices are assembled, rasterization rules, blending — into one object the GPU can execute efficiently. This is also where dynamic rendering gets wired in, replacing the render pass a traditional pipeline would reference.

## Shader stages

```python
vert_module, vert_buf = self.load_shader("shaders/hello_triangle.vert.spv")
frag_module, frag_buf = self.load_shader("shaders/hello_triangle.frag.spv")

vert_stage = VkPipelineShaderStageCreateInfo(stage=VkShaderStageFlagBits.VK_SHADER_STAGE_VERTEX_BIT, module=vert_module, pName=b"main")
frag_stage = VkPipelineShaderStageCreateInfo(stage=VkShaderStageFlagBits.VK_SHADER_STAGE_FRAGMENT_BIT, module=frag_module, pName=b"main")
stages = (VkPipelineShaderStageCreateInfo * 2)(vert_stage, frag_stage)
```

`pName=b"main"` is the entry point function name inside the SPIR-V module — GLSL's `main()` compiles to a function Vulkan looks up by name, so this has to match whatever your shader's entry function is actually called.

## Vertex input — empty, on purpose

The hello-triangle shaders from Chapter 7 read no vertex attributes at all (positions and colors are hardcoded, indexed by `gl_VertexIndex`), so this state simply declares zero bindings and zero attributes:

```python
vertex_input = VkPipelineVertexInputStateCreateInfo(
    vertexBindingDescriptionCount=0,
    vertexAttributeDescriptionCount=0,
)
```

Part 2 is where this struct grows a binding description and attribute descriptions once real vertex buffers enter the picture.

## Input assembly, viewport, and scissor

```python
input_assembly = VkPipelineInputAssemblyStateCreateInfo(topology=VkPrimitiveTopology.VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST)

viewport = VkViewport(
    x=0.0, y=0.0, width=float(self.swapchain_extent.width),
    height=float(self.swapchain_extent.height), minDepth=0.0, maxDepth=1.0
)
scissor = VkRect2D(offset=VkOffset2D(x=0, y=0), extent=self.swapchain_extent)
dynamic_states = [VkDynamicState.VK_DYNAMIC_STATE_VIEWPORT, VkDynamicState.VK_DYNAMIC_STATE_SCISSOR]
dyn_states_arr = (c_int32 * len(dynamic_states))(*dynamic_states)
dyn_state = VkPipelineDynamicStateCreateInfo(
    dynamicStateCount=len(dynamic_states),
    pDynamicStates=cast(dyn_states_arr, POINTER(c_int32))
)
viewport_state = VkPipelineViewportStateCreateInfo(
    viewportCount=1, pViewports=pointer(viewport),
    scissorCount=1, pScissors=pointer(scissor)
)
```

**Dynamic viewport/scissor:** listing these in `dynamic_states` means the actual values get set later with `vkCmdSetViewport`/`vkCmdSetScissor` per-frame, instead of being baked into the pipeline. That's what lets the window resize without rebuilding the entire pipeline — only the swap chain needs recreating.

> Vulkan's clip space is Y-down by default (top of screen is `-1`, not `+1` like OpenGL) — for a flat-colored triangle that just mirrors it vertically, harmless for now. Part 2 covers the fix once an MVP camera transform is in play and the flip actually matters.

## Rasterizer, multisampling, and blending

```python
rasterizer = VkPipelineRasterizationStateCreateInfo(
    polygonMode=VkPolygonMode.VK_POLYGON_MODE_FILL,
    cullMode=VkCullModeFlagBits.VK_CULL_MODE_BACK_BIT,
    frontFace=VkFrontFace.VK_FRONT_FACE_CLOCKWISE,
    lineWidth=1.0
)

multisampling = VkPipelineMultisampleStateCreateInfo(rasterizationSamples=VkSampleCountFlagBits.VK_SAMPLE_COUNT_1_BIT)

color_blend_attachment = VkPipelineColorBlendAttachmentState(blendEEnable=0, colorWriteMask=0xF)
color_blend = VkPipelineColorBlendStateCreateInfo(attachmentCount=1, pAttachments=pointer(color_blend_attachment))
```

`frontFace=CLOCKWISE` has to agree with whatever winding order your vertices actually go in, or back-face culling silently discards the wrong triangles. Blending is off (`blendEEnable=0`) since this triangle is fully opaque — `colorWriteMask=0xF` just means "write to all four color channels" (RGBA).

## Pipeline layout — empty, on purpose

No descriptor sets or push constants exist yet in Part 1, so the layout is as bare as it gets:

```python
layout_info = VkPipelineLayoutCreateInfo(
    setLayoutCount=0,
    pSetLayouts=None,
    pushConstantRangeCount=0
)
pipeline_layout = VkPipelineLayout()
check(self.device.vkCreatePipelineLayout(layout_info, None, byref(pipeline_layout)), "vkCreatePipelineLayout")
self.pipeline_layout = pipeline_layout
```

## Wiring in dynamic rendering

Instead of referencing a `VkRenderPass`, the pipeline gets told what attachment formats it'll be rendering to via `VkPipelineRenderingCreateInfo`, chained through `pNext`:

```python
color_format = c_int32(self.swapchain_format)
rendering_create_info = VkPipelineRenderingCreateInfo(
    colorAttachmentCount=1, pColorAttachmentFormats=pointer(color_format)
)
```

This is the pipeline-side counterpart to the `dynamicRendering=1` feature enabled back in Chapter 5 — it's what lets `vkCmdBeginRendering` (Chapter 10) target the swap chain images directly, with no framebuffer object in between.

## Creating the pipeline

```python
pipeline_info = VkGraphicsPipelineCreateInfo(
    pNext=cast(pointer(rendering_create_info), c_void_p),
    stageCount=2, pStages=cast(stages, POINTER(VkPipelineShaderStageCreateInfo)),
    pVertexInputState=pointer(vertex_input),
    pInputAssemblyState=pointer(input_assembly),
    pViewportState=pointer(viewport_state),
    pDynamicState=pointer(dyn_state),
    pRasterizationState=pointer(rasterizer),
    pMultisampleState=pointer(multisampling),
    pColorBlendState=pointer(color_blend),
    layout=pipeline_layout,
)
pipeline = VkPipeline()
check(self.device.vkCreateGraphicsPipelines(VkPipelineCache(0), 1, byref(pipeline_info), None, byref(pipeline)), "vkCreateGraphicsPipelines")
self.pipeline = pipeline

self.device.vkDestroyShaderModule(vert_module, None)
self.device.vkDestroyShaderModule(frag_module, None)
```

`VkPipelineCache(0)` means "no cache" — fine for a single pipeline built once at startup; a real app creating many pipelines would want a real cache to speed up repeated compilation. Once the pipeline exists, the shader modules that fed into it can be destroyed immediately — the pipeline has already consumed and compiled them, so there's nothing left that needs the modules to stick around.

[← Back to index](README.md) · Previous: [Shader Modules](07-shader-modules.md) · Next: [Command Pool & Buffers →](09-command-buffers.md)