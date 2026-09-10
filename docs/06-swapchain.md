# 6. Swap Chain & Image Views

[← Back to index](README.md) · Previous: [Logical Device & Queues](05-logical-device.md) · Next: [Shader Modules →](07-shader-modules.md)

The **swap chain** is a queue of images the GPU renders into and the platform presents to screen. Setting it up means querying what the surface actually supports, then picking sane defaults from those options.

## Surface capabilities, format, and present mode

```python
caps = VkSurfaceCapabilitiesKHR()
self.instance.vkGetPhysicalDeviceSurfaceCapabilitiesKHR(self.physical_device, self.surface, byref(caps))

fmt_count = c_uint32(0)
self.instance.vkGetPhysicalDeviceSurfaceFormatsKHR(self.physical_device, self.surface, byref(fmt_count), None)
formats = (VkSurfaceFormatKHR * fmt_count.value)()
self.instance.vkGetPhysicalDeviceSurfaceFormatsKHR(self.physical_device, self.surface, byref(fmt_count), formats)
chosen_format = formats[0]
for f in formats:
    if (f.format == VkFormat.VK_FORMAT_B8G8R8A8_UNORM
            and f.colorSpace == VkColorSpaceKHR.VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
        chosen_format = f
        break

mode_count = c_uint32(0)
self.instance.vkGetPhysicalDeviceSurfacePresentModesKHR(self.physical_device, self.surface, byref(mode_count), None)
modes = (ctypes.c_int32 * mode_count.value)()
self.instance.vkGetPhysicalDeviceSurfacePresentModesKHR(self.physical_device, self.surface, byref(mode_count), modes)
if VkPresentModeKHR.VK_PRESENT_MODE_IMMEDIATE_KHR in list(modes):
    present_mode = VkPresentModeKHR.VK_PRESENT_MODE_IMMEDIATE_KHR
elif VkPresentModeKHR.VK_PRESENT_MODE_MAILBOX_KHR in list(modes):
    present_mode = VkPresentModeKHR.VK_PRESENT_MODE_MAILBOX_KHR
else:
    present_mode = VkPresentModeKHR.VK_PRESENT_MODE_FIFO_KHR
```

`VK_FORMAT_B8G8R8A8_UNORM` + SRGB is falling back to `formats[0]` if that exact combo isn't offered — good enough for a tutorial, though a real app should score *all* returned formats rather than assume. Present mode falls back through immediate → mailbox → FIFO; FIFO is the one mode every Vulkan implementation is guaranteed to support (it's basically vsync), so it's always available as the last resort.

## Extent and image count

```python
if caps.currentExtent.width != 0xFFFFFFFF:
    extent = caps.currentExtent
else:
    fb_w, fb_h = glfw.get_framebuffer_size(self.window)
    extent = VkExtent2D(width=fb_w, height=fb_h)

image_count = caps.minImageCount + 1
if caps.maxImageCount != 0 and image_count > caps.maxImageCount:
    image_count = caps.maxImageCount
```

`0xFFFFFFFF` as `currentExtent.width` is the surface telling you "the window manager doesn't dictate a size — you decide," which is when the actual framebuffer size gets used instead. Requesting `minImageCount + 1` rather than the bare minimum avoids stalling on the driver while waiting for an image to free up.

## Sharing mode

```python
if self.graphics_family != self.present_family:
    indices = (c_uint32 * 2)(self.graphics_family, self.present_family)
    sharing_mode, index_count, indices_ptr = VkSharingMode.VK_SHARING_MODE_CONCURRENT, 2, cast(indices, POINTER(c_uint32))
else:
    sharing_mode, index_count, indices_ptr = VkSharingMode.VK_SHARING_MODE_EXCLUSIVE, 0, None
```

If graphics and present are different queue families, images need `CONCURRENT` sharing so both queues can touch them without manual ownership transfers. Same family → `EXCLUSIVE`, which is both simpler and faster.

## Creating the swap chain

```python
create_info = VkSwapchainCreateInfoKHR(
    surface=self.surface,
    minImageCount=image_count,
    imageFormat=chosen_format.format,
    imageColorSpace=chosen_format.colorSpace,
    imageExtent=extent,
    imageArrayLayers=1,
    imageUsage=VkImageUsageFlagBits.VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
    imageSharingMode=sharing_mode,
    queueFamilyIndexCount=index_count,
    pQueueFamilyIndices=indices_ptr,
    preTransform=caps.currentTransform,
    compositeAlpha=VkCompositeAlphaFlagBitsKHR.VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
    presentMode=present_mode,
    clipped=1,
    oldSwapchain=VkSwapchainKHR(0),
)

swapchain = VkSwapchainKHR()
check(self.device.vkCreateSwapchainKHR(create_info, None, byref(swapchain)), "vkCreateSwapchainKHR")
self.swapchain, self.swapchain_format, self.swapchain_extent = swapchain, chosen_format.format, extent

img_count = c_uint32(0)
self.device.vkGetSwapchainImagesKHR(self.swapchain, byref(img_count), None)
images = (VkImage * img_count.value)()
self.device.vkGetSwapchainImagesKHR(self.swapchain, byref(img_count), images)
self.swapchain_images = list(images)
```

`oldSwapchain=VkSwapchainKHR(0)` means "this is a fresh swap chain, not replacing one from a resize" — a real resize-handling path would pass the previous swapchain handle here instead, letting the driver recycle resources.

## Image views

Swap chain images can't be used directly as render targets — a `VkImageView` describes *how* to interpret an image (format, which mip levels/layers), and it's the view that pipeline and rendering commands actually reference:

```python
self.swapchain_image_views = []
for img in self.swapchain_images:
    create_info = VkImageViewCreateInfo(
        image=img,
        viewType=VkImageViewType.VK_IMAGE_VIEW_TYPE_2D,
        format=self.swapchain_format,
        components=VkComponentMapping(
            r=VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
            g=VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
            b=VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
            a=VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
        ),
        subresourceRange=VkImageSubresourceRange(
            aspectMask=VkImageAspectFlagBits.VK_IMAGE_ASPECT_COLOR_BIT,
            baseMipLevel=0, levelCount=1, baseArrayLayer=0, layerCount=1
        )
    )
    view = VkImageView()
    check(self.device.vkCreateImageView(create_info, None, byref(view)), "vkCreateImageView")
    self.swapchain_image_views.append(view)
```

`VK_COMPONENT_SWIZZLE_IDENTITY` on all four channels means "don't remap anything" — R stays R, G stays G, and so on. One view gets created per swap chain image, and this list is what Chapter 12's draw loop renders into via `vkCmdBeginRendering` instead of the framebuffers a render-pass-based approach would use.

[← Back to index](README.md) · Previous: [Logical Device & Queues](05-logical-device.md) · Next: [Shader Modules →](07-shader-modules.md)