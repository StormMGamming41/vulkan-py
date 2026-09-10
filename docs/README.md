# vulkan_py — Tutorial

> **Note on this guide:** Vulkan's modern way to render — **dynamic rendering** (`VK_KHR_dynamic_rendering`, core since 1.3) — is what this whole guide is built around. It skips `VkRenderPass` and `VkFramebuffer` objects entirely in favor of `vkCmdBeginRendering` / `vkCmdEndRendering`, with explicit image layout transitions (`VkImageMemoryBarrier2` + `vkCmdPipelineBarrier2`) taking over the job render passes used to do implicitly. If you're looking at other Vulkan tutorials (including the excellent vulkan-tutorial.com, which this guide's structure is loosely based on) and see `VkRenderPass`/`VkFramebuffer` code, that's the **traditional, render-pass-based** approach — an older but still valid way of doing the same thing. The two aren't mixed together here, so don't expect to see render passes in this guide.

## Prerequisites

- Vulkan SDK installed (provides `glslc`, validation layers)
- GLFW, `numpy`, `pyrr`
- `pip install vulkan_py`
- A `shaders/` directory next to your script, holding compiled `.spv` shaders

## Before you start

`vulkan_py` is ctypes-based, and ctypes is strict about types — passing plain `None` where Vulkan itself would accept a null handle sometimes raises a type error instead of just working. Where that happens, pass a zeroed handle of the actual type Vulkan expects instead, the way this guide does in a few places already (e.g. `VkSwapchainKHR(0)` for "no old swapchain", `VkPipelineCache(0)` for "no pipeline cache"). If you hit this and aren't sure what to zero, or run into any other issue following along, feel free to reach out — [open an issue on GitHub](https://github.com/StormMGamming41/Vulkan-vk-xml-to-py-parser/issues) and I'll help sort it out.

**Running the script partway through the tutorial:** `cleanup()` (Chapter 11) is only complete once every chapter is implemented. If you want to run and test your code before reaching the end, make sure `cleanup()` at that point only destroys the objects you've actually created so far — running without destroying everything you've created leaks GPU memory, and the validation layer (Chapter 2) will flag it with warnings every time. Comment out or remove any destroy calls for objects from chapters you haven't gotten to yet, and add them back in as you go.

## Part 1 — Hello Triangle

Straightforward, no descriptor sets or buffers — a hardcoded triangle on screen, same scope as the classic Vulkan "hello triangle."

1. [Instance Creation](01-instance.md)
2. [Debug Messenger](02-debug-messenger.md)
3. [Window Surface](03-surface.md)
4. [Physical Device Selection](04-physical-device.md)
5. [Logical Device & Queues](05-logical-device.md)
6. [Swap Chain & Image Views](06-swapchain.md)
7. [Shader Modules](07-shader-modules.md)
8. [Graphics Pipeline (Dynamic Rendering)](08-pipeline.md)
9. [Command Pool & Buffers](09-command-buffers.md)
10. [Sync Objects & The Draw Loop](10-sync-and-draw-loop.md)
11. [Cleanup](11-cleanup.md)

## Part 2 — 3D Rendering *(coming soon)*

Builds on Part 1's triangle: vertex/index buffers, uniform buffers, descriptor sets, an MVP camera transform, and a point light.

Each chapter builds directly on the last, following `init_vulkan()`'s call order. By the end of Part 1 you'll have a triangle rendering via dynamic rendering with proper teardown; Part 2 turns it into a lit, camera-driven 3D scene.