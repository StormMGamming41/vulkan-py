# 5. Logical Device & Queues

[← Back to index](README.md) · Previous: [Physical Device Selection](04-physical-device.md) · Next: [Swap Chain & Image Views →](06-swapchain.md)

The physical device is just hardware Vulkan knows about — a **logical device** (`VkDevice`) is what you actually issue commands through. This is also where you opt into `VK_KHR_dynamic_rendering`-related features.

## Queue create infos

You need one `VkDeviceQueueCreateInfo` per *unique* queue family — if the graphics and present families turned out to be the same index (common on many GPUs), you only request one queue, not two:

```python
unique_families = {self.graphics_family, self.present_family}
priority = c_float(1.0)
queue_infos = [
    VkDeviceQueueCreateInfo(queueFamilyIndex=fam, queueCount=1, pQueuePriorities=pointer(priority))
    for fam in unique_families
]
queue_infos_arr = (VkDeviceQueueCreateInfo * len(queue_infos))(*queue_infos)
```

## Opting into dynamic rendering

This is the one struct in the whole guide that makes dynamic rendering possible at all. `VkPhysicalDeviceVulkan13Features` is chained onto the device create info via `pNext`, requesting both `dynamicRendering` and `synchronization2` (the barrier-based sync used for image layout transitions later):

```python
exts = [b"VK_KHR_swapchain"]
ext_arr = (c_char_p * len(exts))(*exts)
features = VkPhysicalDeviceFeatures()

vk13_features = VkPhysicalDeviceVulkan13Features(
    dynamicRendering=1,
    synchronization2=1
)
```

> Without `dynamicRendering=1` here, every `vkCmdBeginRendering` call from Chapter 12 onward would simply fail — this is the single point where the guide's whole approach gets switched on.

## Creating the device

```python
create_info = VkDeviceCreateInfo(
    pNext=cast(pointer(vk13_features), c_void_p),
    queueCreateInfoCount=len(queue_infos),
    pQueueCreateInfos=cast(queue_infos_arr, POINTER(VkDeviceQueueCreateInfo)),
    enabledExtensionCount=len(exts),
    ppEnabledExtensionNames=cast(ext_arr, POINTER(c_char_p)),
    pEnabledFeatures=pointer(features)
)

raw_device = VkDevice()
check(self.instance.vkCreateDevice(self.physical_device, create_info, None, raw_device), "vkCreateDevice")
self.raw_device = raw_device
self.device = Device(raw_device)
```

Same pattern as instance creation in Chapter 1: `self.instance.vkCreateDevice(...)` dispatches through the instance wrapper (device creation is still an instance-level call), but the result — `raw_device` — gets wrapped in its own `Device(raw_device)`. From here on, every device-level command (buffers, pipelines, command buffers, drawing) dispatches through `self.device` instead of `self.instance`.

## Retrieving the queues

The device doesn't hand you queues automatically — you fetch handles to the ones you requested:

```python
graphics_queue = VkQueue()
self.device.vkGetDeviceQueue(self.graphics_family, 0, byref(graphics_queue))
self.graphics_queue = graphics_queue

present_queue = VkQueue()
self.device.vkGetDeviceQueue(self.present_family, 0, byref(present_queue))
self.present_queue = present_queue
```

The `0` here is the queue *index* within the family, not the family index itself — since only one queue per family was requested above, it's always `0`. `self.graphics_queue` is what you'll submit rendering command buffers to later; `self.present_queue` is what actually presents a finished frame to the screen.

[← Back to index](README.md) · Previous: [Physical Device Selection](04-physical-device.md) · Next: [Swap Chain & Image Views →](06-swapchain.md)