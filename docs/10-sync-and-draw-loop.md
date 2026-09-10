# 10. Sync Objects & The Draw Loop

[← Back to index](README.md) · Previous: [Command Pool & Buffers](09-command-buffers.md) · Next: [Cleanup →](11-cleanup.md)

Everything so far has set the stage — this is where a frame actually gets drawn. The CPU and GPU run asynchronously, so this chapter starts with the sync primitives that keep them from stepping on each other, then walks through recording a frame and submitting it.

## Semaphores and fences

Two different sync primitives are used for two different jobs: **semaphores** coordinate GPU-to-GPU work (one queue operation waiting on another), while **fences** let the CPU wait on the GPU:

```python
self.render_semaphores = []
for img in self.swapchain_images:
    render_semaphore = VkSemaphore()
    check(self.device.vkCreateSemaphore(VkSemaphoreCreateInfo(), None, byref(render_semaphore)), "vkCreateSemaphore")
    self.render_semaphores.append(render_semaphore)

self.present_complete_semaphores = []
self.in_flight_fences = []
for i in range(MAX_FRAMES_IN_FLIGHT):
    present_semaphore = VkSemaphore()
    check(self.device.vkCreateSemaphore(VkSemaphoreCreateInfo(), None, byref(present_semaphore)), "vkCreateSemaphore")
    self.present_complete_semaphores.append(present_semaphore)

    fence_info = VkFenceCreateInfo(flags=VkFenceCreateFlagBits.VK_FENCE_CREATE_SIGNALED_BIT)
    draw_fence = VkFence()
    check(self.device.vkCreateFence(fence_info, None, byref(draw_fence)), "vkCreateFence")
    self.in_flight_fences.append(draw_fence)

self.frame_index = 0
```

Note the asymmetry: one render semaphore *per swap chain image*, but one present-complete semaphore and one fence *per frame-in-flight*. That's because a render semaphore has to stay tied to whichever specific image it signals completion for, while the in-flight tracking only needs to know about `MAX_FRAMES_IN_FLIGHT` frames at a time. `VK_FENCE_CREATE_SIGNALED_BIT` starts every fence already signaled — otherwise the very first frame would deadlock waiting on a fence nothing has signaled yet.

## Image layout transitions

Without a render pass to handle it implicitly, dynamic rendering needs *you* to transition the swap chain image's layout by hand — both before rendering (undefined → attachment) and after (attachment → present-ready). One helper handles both directions via `VkImageMemoryBarrier2`:

```python
def transition_image(self, cmd, img_index, old_layout, new_layout,
    src_access_mask, dst_access_mask, src_stage_mask, dst_stage_mask):

    barrier = VkImageMemoryBarrier2(
        srcStageMask=src_stage_mask,
        srcAccessMask=src_access_mask,
        dstStageMask=dst_stage_mask,
        dstAccessMask=dst_access_mask,
        oldLayout=old_layout,
        newLayout=new_layout,
        srcQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
        dstQueueFamilyIndex=VK_QUEUE_FAMILY_IGNORED,
        image=self.swapchain_images[img_index.value],
        subresourceRange=VkImageSubresourceRange(
            aspectMask=VkImageAspectFlagBits.VK_IMAGE_ASPECT_COLOR_BIT,
            baseMipLevel=0,
            levelCount=1,
            baseArrayLayer=0,
            layerCount=1
        )
    )
    dep_info = VkDependencyInfo(
        imageMemoryBarrierCount=1,
        pImageMemoryBarriers=pointer(barrier)
    )
    self.device.vkCmdPipelineBarrier2(cmd, byref(dep_info))
```

`VK_QUEUE_FAMILY_IGNORED` for both queue family fields means this barrier isn't transferring ownership between queue families — just changing layout on the same queue. `vkCmdPipelineBarrier2` (the "2" matters — this is the `synchronization2` version enabled back in Chapter 5) is what makes this a single, simpler call instead of the older, more error-prone `vkCmdPipelineBarrier`.

## Recording a frame

```python
def record_command_buffer(self, image_index):

    begin_info = VkCommandBufferBeginInfo()
    check(self.device.vkBeginCommandBuffer(self.command_buffers[self.frame_index], begin_info), "vkBeginCommandBuffer")

    self.transition_image(
        cmd=self.command_buffers[self.frame_index], img_index=image_index,
        old_layout=VkImageLayout.VK_IMAGE_LAYOUT_UNDEFINED,
        new_layout=VkImageLayout.VK_IMAGE_LAYOUT_ATTACHMENT_OPTIMAL,
        src_access_mask=0,
        dst_access_mask=VkAccessFlagBits2.VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT,
        src_stage_mask=VkPipelineStageFlagBits2.VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT,
        dst_stage_mask=VkPipelineStageFlagBits2.VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT
    )
    clear_color = VkClearValue(color=VkClearColorValue(float32=(0.1, 0.1, 0.1, 1.0)))

    attachment_info = VkRenderingAttachmentInfo(
        imageView=self.swapchain_image_views[image_index.value],
        imageLayout=VkImageLayout.VK_IMAGE_LAYOUT_ATTACHMENT_OPTIMAL,
        loadOp=VkAttachmentLoadOp.VK_ATTACHMENT_LOAD_OP_CLEAR,
        storeOp=VkAttachmentStoreOp.VK_ATTACHMENT_STORE_OP_STORE,
        clearValue=clear_color
    )

    render_info = VkRenderingInfo(
        renderArea=VkRect2D(VkOffset2D(x=0, y=0), self.swapchain_extent),
        layerCount=1,
        colorAttachmentCount=1,
        pColorAttachments=pointer(attachment_info)
    )

    viewport = VkViewport(
        x=0.0, y=0.0, width=float(self.swapchain_extent.width),
        height=float(self.swapchain_extent.height), minDepth=0.0, maxDepth=1.0
    )
    scissor = VkRect2D(VkOffset2D(x=0, y=0), self.swapchain_extent)

    self.device.vkCmdBeginRendering(self.command_buffers[self.frame_index], render_info)

    self.device.vkCmdBindPipeline(self.command_buffers[self.frame_index], VkPipelineBindPoint.VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)
    self.device.vkCmdSetViewport(self.command_buffers[self.frame_index], 0, 1, viewport)
    self.device.vkCmdSetScissor(self.command_buffers[self.frame_index], 0, 1, scissor)
    self.device.vkCmdDraw(self.command_buffers[self.frame_index], 3, 1, 0, 0)

    self.device.vkCmdEndRendering(self.command_buffers[self.frame_index])

    self.transition_image(
        cmd=self.command_buffers[self.frame_index], img_index=image_index,
        old_layout=VkImageLayout.VK_IMAGE_LAYOUT_ATTACHMENT_OPTIMAL,
        new_layout=VkImageLayout.VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
        src_access_mask=VkAccessFlagBits2.VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT,
        dst_access_mask=VkAccessFlagBits2.VK_ACCESS_2_NONE,
        src_stage_mask=VkPipelineStageFlagBits2.VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT,
        dst_stage_mask=VkPipelineStageFlagBits2.VK_PIPELINE_STAGE_2_NONE
    )

    check(self.device.vkEndCommandBuffer(self.command_buffers[self.frame_index]), "vkEndCommandBuffer")
```

A few things worth tracing through:

- **`vkCmdBeginRendering`/`vkCmdEndRendering`** bracket the actual draw commands — this pair is dynamic rendering's direct replacement for `vkCmdBeginRenderPass`/`vkCmdEndRenderPass`.
- The **first transition** (`UNDEFINED → ATTACHMENT_OPTIMAL`) happens before rendering, and the **second** (`ATTACHMENT_OPTIMAL → PRESENT_SRC_KHR`) happens after — the image has to be in the right layout for each stage of its life, and dynamic rendering makes both transitions your responsibility instead of the render pass's.
- Since there's no vertex buffer or descriptor set in Part 1, the draw call is just `vkCmdDraw(cmd, 3, 1, 0, 0)` — 3 vertices, 1 instance, no offsets — relying entirely on the hardcoded positions in `hello_triangle.vert` from Chapter 7.
- Viewport and scissor get set here, per-frame, via `vkCmdSetViewport`/`vkCmdSetScissor` — this is what the pipeline's `VK_DYNAMIC_STATE_VIEWPORT`/`SCISSOR` from Chapter 8 was setting up for.

## The draw loop itself

```python
def draw_frame(self):

    fences = self.in_flight_fences[self.frame_index]
    self.device.vkWaitForFences(1, byref(fences), VK_TRUE, UINT64_MAX)

    image_index = c_uint32(0)
    img_result = self.device.vkAcquireNextImageKHR(self.swapchain, UINT64_MAX, self.present_complete_semaphores[self.frame_index], VkFence(0), byref(image_index))
    if img_result == VkResult.VK_ERROR_OUT_OF_DATE_KHR:
        self.recreate_swapchain()
        return None
    elif (img_result != VkResult.VK_SUCCESS) and (img_result != VkResult.VK_SUBOPTIMAL_KHR):
        raise RuntimeError("Failed to acquire swapchain image index")

    self.device.vkResetFences(1, byref(fences))

    self.device.vkResetCommandBuffer(self.command_buffers[self.frame_index], 0)
    self.record_command_buffer(image_index)

    wait_semaphores = (VkSemaphore * 1)(self.present_complete_semaphores[self.frame_index])
    signal_semaphores = (VkSemaphore * 1)(self.render_semaphores[image_index.value])
    wait_stages = (c_uint32 * 1)(VkPipelineStageFlagBits.VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT)
    cmd_buffers = (VkCommandBuffer * 1)(self.command_buffers[self.frame_index])

    submit_info = VkSubmitInfo(
        waitSemaphoreCount=1, pWaitSemaphores=cast(wait_semaphores, POINTER(VkSemaphore)),
        pWaitDstStageMask=cast(wait_stages, POINTER(ctypes.c_uint32)),
        commandBufferCount=1, pCommandBuffers=cast(cmd_buffers, POINTER(VkCommandBuffer)),
        signalSemaphoreCount=1, pSignalSemaphores=cast(signal_semaphores, POINTER(VkSemaphore)),
    )

    check(self.device.vkQueueSubmit(self.graphics_queue, 1, byref(submit_info), fences), "vkQueueSubmit")

    swapchains = (VkSwapchainKHR * 1)(self.swapchain)
    present_info = VkPresentInfoKHR(
        waitSemaphoreCount=1, pWaitSemaphores=cast(signal_semaphores, POINTER(VkSemaphore)),
        swapchainCount=1, pSwapchains=cast(swapchains, POINTER(VkSwapchainKHR)),
        pImageIndices=pointer(image_index),
    )
    present_result = self.device.vkQueuePresentKHR(self.present_queue, byref(present_info))
    if (present_result == VkResult.VK_ERROR_OUT_OF_DATE_KHR) or (present_result == VkResult.VK_SUBOPTIMAL_KHR) or self.framebuffer_resized:
        self.recreate_swapchain()
        self.framebuffer_resized = False
    elif present_result != VkResult.VK_SUCCESS:
        raise RuntimeError("Failed to present the present queue")

    self.frame_index = (self.frame_index + 1) % MAX_FRAMES_IN_FLIGHT
```

Walking the sequence: wait for this frame slot's fence (so the CPU doesn't outrun the GPU by more than `MAX_FRAMES_IN_FLIGHT` frames) → acquire the next swap chain image → reset the fence and command buffer → record → submit (waiting on `present_complete_semaphores`, signaling `render_semaphores`) → present (waiting on that same render semaphore, so presentation can't happen before rendering finishes).

`VK_ERROR_OUT_OF_DATE_KHR` shows up in two places — acquiring the image and presenting — because the window can be resized (or otherwise invalidate the swap chain) between those two calls. Handling it in both spots, plus checking `self.framebuffer_resized` after presenting, is what makes resizing the window not crash the app:

```python
def recreate_swapchain(self):

    width, height = glfw.get_framebuffer_size(self.window)
    while (width == 0) or (height == 0):
        width, height = glfw.get_framebuffer_size(self.window)
        glfw.wait_events()

    self.device.vkDeviceWaitIdle()

    self.cleanup_swapchain()

    self.create_swapchain()
    self.create_image_views()
```

The `while` loop handles minimization specifically — a minimized window reports a `0×0` framebuffer, and creating a swap chain with zero size is invalid, so it just waits until the window has a real size again.

## Tying it together

```python
def main_loop(self):

    while not glfw.window_should_close(self.window):
        glfw.poll_events()
        self.draw_frame()

    self.device.vkDeviceWaitIdle()
```

`vkDeviceWaitIdle()` after the loop exits matters more than it looks — without it, cleanup in the next chapter could start destroying objects the GPU is still actively using.

[← Back to index](README.md) · Previous: [Command Pool & Buffers](09-command-buffers.md) · Next: [Cleanup →](11-cleanup.md)