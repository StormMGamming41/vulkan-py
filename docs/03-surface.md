# 3. Window Surface

[← Back to index](README.md) · Previous: [Debug Messenger](02-debug-messenger.md) · Next: [Physical Device Selection →](04-physical-device.md)

Vulkan itself has no idea what a "window" is — that's the platform's job. A `VkSurfaceKHR` is the bridge between your GLFW window and something Vulkan can actually render into.

## Creating the surface

GLFW ships its own helper that wraps the platform-specific surface creation (Win32, Xlib/Wayland, etc.) behind one call, so you don't have to branch on OS yourself:

```python
from ctypes import c_void_p

surface_handle = c_void_p(0)
check(
    glfw.create_window_surface(self.raw_instance.value, self.window, None, byref(surface_handle)),
    "glfw.create_window_surface"
)
self.surface = VkSurfaceKHR(surface_handle.value)
```

A couple of details worth noting:

- This call needs the **raw** instance handle (`self.raw_instance.value` from Chapter 1) — GLFW's helper isn't part of `vulkan_py`'s wrapper, it talks directly to the C API, so it wants the underlying handle rather than the `Instance` wrapper object.
- GLFW's function returns a plain Vulkan result code, so `check()` still works here exactly the same as it does for `vulkan_py` calls — `0` is `VK_SUCCESS` either way.
- The window itself (`self.window`) has to already exist — this is why `init_window()` runs before `init_vulkan()`.

That's it for this chapter — short, but everything from here on (swap chain, presentation, framebuffer size) depends on this surface existing.

[← Back to index](README.md) · Previous: [Debug Messenger](02-debug-messenger.md) · Next: [Physical Device Selection →](04-physical-device.md)