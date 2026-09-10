# 9. Command Pool & Buffers

[← Back to index](README.md) · Previous: [Graphics Pipeline](08-pipeline.md) · Next: [Sync Objects & The Draw Loop →](10-sync-and-draw-loop.md)

GPU work isn't issued command-by-command like a typical API call — it's recorded into a **command buffer** first, then submitted to a queue all at once. Command buffers are allocated from a **command pool**, which is tied to a specific queue family.

## Creating the command pool

```python
pool_info = VkCommandPoolCreateInfo(
    flags=VkCommandPoolCreateFlagBits.VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    queueFamilyIndex=self.graphics_family
)
command_pool = VkCommandPool()
check(self.device.vkCreateCommandPool(pool_info, None, byref(command_pool)), "vkCreateCommandPool")
self.command_pool = command_pool
```

`queueFamilyIndex=self.graphics_family` ties this pool to the graphics queue family from Chapter 4 — every command buffer allocated from it can only be submitted to a queue in that same family. `VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT` allows individual command buffers to be reset and re-recorded (rather than needing to reset the whole pool at once), which the per-frame draw loop in the next chapter relies on.

## Allocating command buffers

```python
alloc_info = VkCommandBufferAllocateInfo(
    commandPool=self.command_pool,
    level=VkCommandBufferLevel.VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    commandBufferCount=MAX_FRAMES_IN_FLIGHT
)

buffers = (VkCommandBuffer * MAX_FRAMES_IN_FLIGHT)()
check(self.device.vkAllocateCommandBuffers(alloc_info, buffers), "vkAllocateCommandBuffers")
self.command_buffers = list(buffers)
```

`MAX_FRAMES_IN_FLIGHT` (`= 2` here) is why there are multiple command buffers rather than just one: while the GPU is still working through last frame's commands, the CPU can already be recording the next frame's into a different buffer, instead of stalling and waiting. `VK_COMMAND_BUFFER_LEVEL_PRIMARY` means these are submitted to a queue directly — a *secondary* command buffer, by contrast, can only be called from within a primary one, which is a pattern for splitting up recording work rather than something this guide uses.

Nothing gets recorded into these buffers yet — that happens per-frame in the draw loop, next chapter.

[← Back to index](README.md) · Previous: [Graphics Pipeline](08-pipeline.md) · Next: [Sync Objects & The Draw Loop →](10-sync-and-draw-loop.md)