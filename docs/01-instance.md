# 1. Instance Creation

[← Back to index](README.md) · Next: [Debug Messenger →](02-debug-messenger.md)

Every Vulkan program starts by creating an **instance** — it connects your application to the Vulkan library and tells the driver a bit about what you're building.

## A small helper first

Nearly every Vulkan call in this guide returns a `VkResult`, and nearly every one needs the same check: did it succeed, and if not, fail loudly. Rather than repeat that inline everywhere, define it once up front and reuse it for every Vulkan call from here on:

```python
from vulkan_py import *

def check(result, op):
    if result != VkResult.VK_SUCCESS:
        raise RuntimeError(f"Operation {op} failed execution, result {result}")
```

## Application info

```python
from ctypes import c_char_p, cast, pointer, POINTER, byref
import glfw
from vulkan_py import *

DEBUG_MODE = True

app_info = VkApplicationInfo(
    pApplicationName=b"Hello Triangle",
    applicationVersion=1,
    pEngineName=b"No Engine",
    engineVersion=1,
    apiVersion=(1 << 22) | (3 << 22),
)
```

`VkApplicationInfo` is optional per the spec, but always worth filling in — drivers can use it for compatibility workarounds. `apiVersion` is built by hand here to target **1.3**, since that's what makes dynamic rendering part of core (no extension juggling needed).

## Required extensions and validation layers

GLFW tells you which instance extensions it needs to create a surface later. In debug builds we also add `VK_EXT_debug_utils` (for validation messages) and enable `VK_LAYER_KHRONOS_validation`, which catches the vast majority of Vulkan misuse — wrong struct chains, missing barriers, invalid handles — with clear error messages instead of a silent crash or driver-specific undefined behavior:

```python
exts = glfw.get_required_instance_extensions()
ext_bytes = [ext.encode("utf-8") for ext in exts]
if DEBUG_MODE:
    ext_bytes.append(b"VK_EXT_debug_utils")
ext_arr = (c_char_p * len(ext_bytes))(*ext_bytes)

layers = []
if DEBUG_MODE:
    layers.append(b"VK_LAYER_KHRONOS_validation")
layer_arr = (c_char_p * len(layers))(*layers)
```

## Creating the instance

```python
create_info = VkInstanceCreateInfo(
    pApplicationInfo=pointer(app_info),
    enabledExtensionCount=len(ext_bytes),
    ppEnabledExtensionNames=cast(ext_arr, POINTER(c_char_p)),
    enabledLayerCount=len(layers),
    ppEnabledLayerNames=cast(layer_arr, POINTER(c_char_p))
)

raw_instance = VkInstance()
check(vkCreateInstance(byref(create_info), None, byref(raw_instance)), "vkCreateInstance")

instance = Instance(raw_instance)
```

A couple of things worth calling out:

- `vkCreateInstance` here is the loose, module-level function — it's the one Vulkan call you make before you have anything to dispatch it through.
- `vulkan_py` also gives you back an `Instance(raw_instance)` wrapper. From here on, calls like `instance.vkEnumeratePhysicalDevices(...)` dispatch *through* this wrapper rather than as loose functions — that pattern carries through the whole rest of the guide, and later, `Device(raw_device)` does the same job for device-level calls.
- Keep `raw_instance` around too — you'll need the raw handle (not the wrapper) when GLFW creates your surface in Chapter 3.

[← Back to index](README.md) · Next: [Debug Messenger →](02-debug-messenger.md)