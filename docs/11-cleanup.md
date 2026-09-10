# 11. Cleanup

[← Back to index](README.md) · Previous: [Sync Objects & The Draw Loop](10-sync-and-draw-loop.md)

Vulkan doesn't garbage-collect anything — every object created across this guide needs to be explicitly destroyed, and largely in the **reverse** order it was created in, since later objects often depend on earlier ones still existing.

> Skipping this chapter, or running your script before `cleanup()` covers everything you've built so far, will leak GPU memory and trigger validation warnings (Chapter 2) on every run — the driver won't clean up after you. If you're testing as you go rather than waiting until the end, keep `cleanup()` in sync with whatever chapters you've actually implemented.

## Swap chain teardown

Pulled into its own function since `recreate_swapchain()` (Chapter 10) needs to tear down and rebuild it independently of full app shutdown:

```python
def cleanup_swapchain(self):

    for view in self.swapchain_image_views: self.device.vkDestroyImageView(view, None)
    self.device.vkDestroySwapchainKHR(self.swapchain, None)

    self.swapchain_image_views = []
    self.swapchain = None
```

## Full cleanup

```python
def cleanup(self):

    for s in self.present_complete_semaphores: self.device.vkDestroySemaphore(s, None)
    for s in self.render_semaphores: self.device.vkDestroySemaphore(s, None)
    for f in self.in_flight_fences: self.device.vkDestroyFence(f, None)

    self.device.vkDestroyCommandPool(self.command_pool, None)

    self.device.vkDestroyPipeline(self.pipeline, None)
    self.device.vkDestroyPipelineLayout(self.pipeline_layout, None)

    self.cleanup_swapchain()

    self.device.vkDestroyDevice(None)

    self.instance.vkDestroySurfaceKHR(self.surface, None)
    self.instance.vkDestroyDebugUtilsMessengerEXT(self.debug_messenger, None)
    self.instance.vkDestroyInstance(None)

    glfw.destroy_window(self.window)
    glfw.terminate()
```

The order here isn't arbitrary — it mirrors creation, backwards:

- Sync objects and the command pool go first — nothing later depends on them, and destroying the pool implicitly frees the command buffers allocated from it in Chapter 9, so those don't need a separate destroy call.
- Pipeline and pipeline layout follow — created in Chapter 8, no longer needed once nothing will submit further draw calls.
- The swap chain (Chapter 6) is destroyed via the same `cleanup_swapchain()` used for resizing.
- `vkDestroyDevice(None)` destroys the *logical* device from Chapter 5 — note this call is on `self.device` even though the device itself is what's being destroyed; everything allocated from it (pipeline, command pool, swap chain, etc.) must already be gone by this point, which is exactly why it's this late in the sequence.
- Surface, debug messenger, and instance are all instance-level objects (Chapters 1–3), so they're destroyed via `self.instance` last, in the reverse of how they were created — debug messenger before instance itself, since the messenger depends on the instance existing.
- GLFW's window and library state are cleaned up only after every Vulkan object referencing the window (the surface, chiefly) is gone.

## Running it all

```python
def run(self):

    self.init_window()
    self.init_vulkan()
    self.main_loop()
    self.cleanup()

if __name__ == "__main__":
    app = Hello_Triabgle_App()
    app.run()
```

`init_vulkan()` is the master call list this whole guide has walked through, chapter by chapter — instance, debug messenger, surface, physical/logical device, swap chain, shaders, pipeline, command pool, sync objects. Run this and you've got a triangle rendering through dynamic rendering, with clean teardown on exit.

That's Part 1. Part 2 picks up from here — vertex/index buffers, a uniform buffer, descriptor sets, an MVP camera transform, and a point light — turning this triangle into an actual 3D scene.

[← Back to index](README.md) · Previous: [Sync Objects & The Draw Loop](10-sync-and-draw-loop.md)