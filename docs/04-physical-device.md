# 4. Physical Device Selection

[← Back to index](README.md) · Previous: [Window Surface](03-surface.md) · Next: [Logical Device & Queues →](05-logical-device.md)

A "physical device" is an actual GPU (or software renderer) visible to Vulkan. This chapter enumerates what's available and picks the one to use.

## Enumerating GPUs

Like most "give me a list" calls in Vulkan, this is a two-step dance: call once to get a count, allocate an array of that size, then call again to fill it:

```python
count = c_uint32(0)
self.instance.vkEnumeratePhysicalDevices(byref(count), None)
if count.value < 1:
    raise RuntimeError("Failed to find a Vulkan compatible GPU")
self.physical_devices = (VkPhysicalDevice * count.value)()
self.instance.vkEnumeratePhysicalDevices(byref(count), self.physical_devices)
```

## Checking queue family support

Not every GPU can both render *and* present to your surface — sometimes those are different queue families, sometimes the same one. A small helper checks both for a given device:

```python
def _find_queue_families(self, physical_device):
    count = c_uint32(0)
    self.instance.vkGetPhysicalDeviceQueueFamilyProperties(physical_device, byref(count), None)
    families = (VkQueueFamilyProperties * count.value)()
    self.instance.vkGetPhysicalDeviceQueueFamilyProperties(physical_device, byref(count), families)

    graphics_family = present_family = None
    for i, fam in enumerate(families):
        if fam.queueFlags & VkQueueFlagBits.VK_QUEUE_GRAPHICS_BIT:
            graphics_family = i
        supported = c_uint32(0)
        self.instance.vkGetPhysicalDeviceSurfaceSupportKHR(physical_device, i, self.surface, byref(supported))
        if supported.value:
            present_family = i
        if graphics_family is not None and present_family is not None:
            break
    return graphics_family, present_family
```

This is also why physical device selection (Chapter 4) has to happen *after* surface creation (Chapter 3) — checking present support needs a real surface to check against.

## Scoring and picking the best GPU

With multiple GPUs available (common on laptops with integrated + discrete graphics), a simple score prefers a discrete GPU over integrated, and skips anything that can't satisfy both queue families:

```python
best = None
for pd in self.physical_devices:
    gfx, present = self._find_queue_families(pd)
    if gfx is None or present is None:
        continue
    props = VkPhysicalDeviceProperties()
    self.instance.vkGetPhysicalDeviceProperties(pd, props)
    score = 2 if props.deviceType == VkPhysicalDeviceType.VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU else 1
    if best is None or score > best[0]:
        best = (score, pd, gfx, present, props.deviceName.decode(errors="ignore"))

if best is None:
    raise RuntimeError("No GPU with both graphics and present support found")

_, pd, gfx, present, name = best
self.physical_device, self.graphics_family, self.present_family = pd, gfx, present
print(f"Using GPU: {name} (graphics family={gfx}, present family={present})")
```

Nothing gets created here — `self.physical_device` is just a handle to hardware Vulkan already knows about, plus the two queue family indices you'll need in the next chapter to actually request queues from it.

[← Back to index](README.md) · Previous: [Window Surface](03-surface.md) · Next: [Logical Device & Queues →](05-logical-device.md)