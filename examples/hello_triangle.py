import glfw
import vulkan_py as output
import os
import ctypes
from ctypes import c_uint32, c_uint64, c_void_p, c_float, byref, pointer, cast, POINTER, c_char_p

MAX_FRAMES_IN_FLIGHT = 2
UINT64_MAX = 0xFFFFFFFFFFFFFFFF

def check(result, what):
    if result != output.enums.VkResult.VK_SUCCESS:
        print(f"{what} failed: VkResult={result}")

class App:

    def __init__(self, name='test', res=[800,600]):

        self.res = res
        self.name  = name

    def _debug_callback(self, severity, msg_type, callback_data_ptr, user_data):
        data = callback_data_ptr.contents
        message = data.pMessage.decode(errors="ignore") if data.pMessage else "<no message>"

        if severity >= output.VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT:
            tag = "ERROR"
        elif severity >= output.VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT:
            tag = "WARN"
        else:
            tag = "INFO"

        print(f"[validation:{tag}] {message}")
        return 0   # VK_FALSE - don't abort the call that triggered this

    def init_window(self):
        if not glfw.init():
            raise RuntimeError("glfw.init() failed")
        glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)   # no GL context - we're doing Vulkan
        glfw.window_hint(glfw.RESIZABLE, False)           # resize handling comes later
        self.window = glfw.create_window(self.res[0], self.res[1], self.name, None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("glfw.create_window() failed")

    def create_instance(self):
        app_info = output.VkApplicationInfo(
            pApplicationName=self.name.encode("utf-8"),
            applicationVersion=1,
            pEngineName=b"vulkan_py",
            engineVersion=1,
            apiVersion=(1 << 22),
        )

        required_ext = glfw.get_required_instance_extensions()
        ext_bytes = [e.encode("utf-8") if isinstance(e, str) else e for e in required_ext]
        ext_bytes.append(b"VK_EXT_debug_utils")          # <-- new
        ext_arr = (c_char_p * len(ext_bytes))(*ext_bytes)

        layer_bytes = [b"VK_LAYER_KHRONOS_validation"]
        layer_arr = (c_char_p * len(layer_bytes))(*layer_bytes)

        create_info = output.VkInstanceCreateInfo(
            pApplicationInfo=pointer(app_info),
            enabledExtensionCount=len(ext_bytes),
            ppEnabledExtensionNames=cast(ext_arr, POINTER(c_char_p)),
            enabledLayerCount=len(layer_bytes),
            ppEnabledLayerNames=cast(layer_arr, POINTER(c_char_p)),
        )

        raw_instance = output.VkInstance()
        result = output.vkCreateInstance(byref(create_info), None, byref(raw_instance))
        if result != output.VkResult.VK_SUCCESS:
            # most likely VK_ERROR_LAYER_NOT_PRESENT - SDK's validation layer not installed
            print(f"[!] Instance creation with validation failed ({result}), retrying without it")
            create_info.enabledLayerCount = 0
            create_info.ppEnabledLayerNames = None
            create_info.enabledExtensionCount -= 1  # drop debug_utils too, nothing to feed it
            raw_instance = output.VkInstance()
            result = output.vkCreateInstance(byref(create_info), None, byref(raw_instance))

        check(result, "vkCreateInstance")
        self.raw_instance = raw_instance
        self.instance = output.Instance(raw_instance)

    def create_debug_messenger(self):
        # Keep this CFUNCTYPE instance alive on self - if it gets garbage
        # collected, Vulkan is left holding a dangling function pointer and
        # will crash the next time a validation message fires.
        self._debug_callback_fn = output.PFN_vkDebugUtilsMessengerCallbackEXT(self._debug_callback)

        create_info = output.VkDebugUtilsMessengerCreateInfoEXT(
            messageSeverity=(
                output.VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT
                | output.VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
                | output.VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT
            ),
            messageType=(
                output.VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT
                | output.VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT
                | output.VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT
            ),
            pfnUserCallback=self._debug_callback_fn,
        )

        messenger = output.VkDebugUtilsMessengerEXT()
        result = self.instance.vkCreateDebugUtilsMessengerEXT(create_info, None, byref(messenger))
        check(result, "vkCreateDebugUtilsMessengerEXT")
        self.debug_messenger = messenger

    def create_surface(self):
        surface_handle = c_void_p(0)
        result = glfw.create_window_surface(
            self.raw_instance.value, self.window, None, byref(surface_handle)
        )
        if result != 0:
            raise RuntimeError(f"glfwCreateWindowSurface failed: {result}")
        self.surface = output.VkSurfaceKHR(surface_handle.value)

    def pick_physical_device(self):
        count = c_uint32(0)
        self.instance.vkEnumeratePhysicalDevices(byref(count), None)
        if count.value == 0:
            raise RuntimeError("No Vulkan-capable GPU found")
        devices = (output.VkPhysicalDevice * count.value)()
        self.instance.vkEnumeratePhysicalDevices(byref(count), devices)

        best = None
        for pd in devices:
            gfx, present = self._find_queue_families(pd)
            if gfx is None or present is None:
                continue
            props = output.VkPhysicalDeviceProperties()
            self.instance.vkGetPhysicalDeviceProperties(pd, props)
            score = 2 if props.deviceType == output.VkPhysicalDeviceType.VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU else 1
            if best is None or score > best[0]:
                best = (score, pd, gfx, present, props.deviceName.decode(errors="ignore"))

        if best is None:
            raise RuntimeError("No GPU with both graphics and present support found")

        _, pd, gfx, present, name = best
        self.physical_device, self.graphics_family, self.present_family = pd, gfx, present
        print(f"Using GPU: {name} (graphics family={gfx}, present family={present})")

    def _find_queue_families(self, physical_device):
        count = c_uint32(0)
        self.instance.vkGetPhysicalDeviceQueueFamilyProperties(physical_device, byref(count), None)
        families = (output.VkQueueFamilyProperties * count.value)()
        self.instance.vkGetPhysicalDeviceQueueFamilyProperties(physical_device, byref(count), families)

        graphics_family = present_family = None
        for i, fam in enumerate(families):
            if fam.queueFlags & output.VkQueueFlagBits.VK_QUEUE_GRAPHICS_BIT:
                graphics_family = i
            supported = c_uint32(0)
            self.instance.vkGetPhysicalDeviceSurfaceSupportKHR(physical_device, i, self.surface, byref(supported))
            if supported.value:
                present_family = i
            if graphics_family is not None and present_family is not None:
                break
        return graphics_family, present_family

    def create_logical_device(self):
        unique_families = {self.graphics_family, self.present_family}
        priority = c_float(1.0)
        queue_infos = [
            output.VkDeviceQueueCreateInfo(queueFamilyIndex=fam, queueCount=1, pQueuePriorities=pointer(priority))
            for fam in unique_families
        ]
        queue_infos_arr = (output.VkDeviceQueueCreateInfo * len(queue_infos))(*queue_infos)

        device_extensions = [b"VK_KHR_swapchain"]
        ext_arr = (c_char_p * len(device_extensions))(*device_extensions)
        features = output.VkPhysicalDeviceFeatures()   # nothing extra needed yet

        create_info = output.VkDeviceCreateInfo(
            queueCreateInfoCount=len(queue_infos),
            pQueueCreateInfos=cast(queue_infos_arr, POINTER(output.VkDeviceQueueCreateInfo)),
            enabledExtensionCount=len(device_extensions),
            ppEnabledExtensionNames=cast(ext_arr, POINTER(c_char_p)),
            pEnabledFeatures=pointer(features),
        )

        raw_device = output.VkDevice()
        check(self.instance.vkCreateDevice(self.physical_device, create_info, None, raw_device), "vkCreateDevice")
        self.raw_device = raw_device
        self.device = output.Device(raw_device)

        graphics_queue = output.VkQueue()
        self.device.vkGetDeviceQueue(self.graphics_family, 0, byref(graphics_queue))
        self.graphics_queue = graphics_queue

        present_queue = output.VkQueue()
        self.device.vkGetDeviceQueue(self.present_family, 0, byref(present_queue))
        self.present_queue = present_queue

    def create_swapchain(self):
        caps = output.VkSurfaceCapabilitiesKHR()
        self.instance.vkGetPhysicalDeviceSurfaceCapabilitiesKHR(self.physical_device, self.surface, byref(caps))

        fmt_count = c_uint32(0)
        self.instance.vkGetPhysicalDeviceSurfaceFormatsKHR(self.physical_device, self.surface, byref(fmt_count), None)
        formats = (output.VkSurfaceFormatKHR * fmt_count.value)()
        self.instance.vkGetPhysicalDeviceSurfaceFormatsKHR(self.physical_device, self.surface, byref(fmt_count), formats)
        chosen_format = formats[0]
        for f in formats:
            if (f.format == output.VkFormat.VK_FORMAT_B8G8R8A8_UNORM
                    and f.colorSpace == output.VkColorSpaceKHR.VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
                chosen_format = f
                break

        mode_count = c_uint32(0)
        self.instance.vkGetPhysicalDeviceSurfacePresentModesKHR(self.physical_device, self.surface, byref(mode_count), None)
        modes = (ctypes.c_int32 * mode_count.value)()
        self.instance.vkGetPhysicalDeviceSurfacePresentModesKHR(self.physical_device, self.surface, byref(mode_count), modes)
        present_mode = output.VkPresentModeKHR.VK_PRESENT_MODE_FIFO_KHR   # always guaranteed by the spec
        if output.VkPresentModeKHR.VK_PRESENT_MODE_MAILBOX_KHR in list(modes):
            present_mode = output.VkPresentModeKHR.VK_PRESENT_MODE_MAILBOX_KHR

        if caps.currentExtent.width != 0xFFFFFFFF:
            extent = caps.currentExtent
        else:
            fb_w, fb_h = glfw.get_framebuffer_size(self.window)
            extent = output.VkExtent2D(width=fb_w, height=fb_h)

        image_count = caps.minImageCount + 1
        if caps.maxImageCount != 0 and image_count > caps.maxImageCount:
            image_count = caps.maxImageCount

        if self.graphics_family != self.present_family:
            indices = (c_uint32 * 2)(self.graphics_family, self.present_family)
            sharing_mode, index_count, indices_ptr = output.VkSharingMode.VK_SHARING_MODE_CONCURRENT, 2, cast(indices, POINTER(c_uint32))
        else:
            sharing_mode, index_count, indices_ptr = output.VkSharingMode.VK_SHARING_MODE_EXCLUSIVE, 0, None

        create_info = output.VkSwapchainCreateInfoKHR(
            surface=self.surface,
            minImageCount=image_count,
            imageFormat=chosen_format.format,
            imageColorSpace=chosen_format.colorSpace,
            imageExtent=extent,
            imageArrayLayers=1,
            imageUsage=output.VkImageUsageFlagBits.VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
            imageSharingMode=sharing_mode,
            queueFamilyIndexCount=index_count,
            pQueueFamilyIndices=indices_ptr,
            preTransform=caps.currentTransform,
            compositeAlpha=output.VkCompositeAlphaFlagBitsKHR.VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
            presentMode=present_mode,
            clipped=1,
            oldSwapchain=output.VkSwapchainKHR(0),
        )

        swapchain = output.VkSwapchainKHR()
        check(self.device.vkCreateSwapchainKHR(create_info, None, byref(swapchain)), "vkCreateSwapchainKHR")
        self.swapchain, self.swapchain_format, self.swapchain_extent = swapchain, chosen_format.format, extent

        img_count = c_uint32(0)
        self.device.vkGetSwapchainImagesKHR(self.swapchain, byref(img_count), None)
        images = (output.VkImage * img_count.value)()
        self.device.vkGetSwapchainImagesKHR(self.swapchain, byref(img_count), images)
        self.swapchain_images = list(images)

    def create_image_views(self):
        self.swapchain_image_views = []
        for img in self.swapchain_images:
            create_info = output.VkImageViewCreateInfo(
                image=img,
                viewType=output.VkImageViewType.VK_IMAGE_VIEW_TYPE_2D,
                format=self.swapchain_format,
                components=output.VkComponentMapping(
                    r=output.VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
                    g=output.VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
                    b=output.VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
                    a=output.VkComponentSwizzle.VK_COMPONENT_SWIZZLE_IDENTITY,
                ),
                subresourceRange=output.VkImageSubresourceRange(
                    aspectMask=output.VkImageAspectFlagBits.VK_IMAGE_ASPECT_COLOR_BIT,
                    baseMipLevel=0, levelCount=1, baseArrayLayer=0, layerCount=1,
                ),
            )
            view = output.VkImageView()
            check(self.device.vkCreateImageView(create_info, None, byref(view)), "vkCreateImageView")
            self.swapchain_image_views.append(view)

    def create_render_pass(self):
        color_attachment = output.VkAttachmentDescription(
            format=self.swapchain_format,
            samples=output.VkSampleCountFlagBits.VK_SAMPLE_COUNT_1_BIT,
            loadOp=output.VkAttachmentLoadOp.VK_ATTACHMENT_LOAD_OP_CLEAR,
            storeOp=output.VkAttachmentStoreOp.VK_ATTACHMENT_STORE_OP_STORE,
            stencilLoadOp=output.VkAttachmentLoadOp.VK_ATTACHMENT_LOAD_OP_DONT_CARE,
            stencilStoreOp=output.VkAttachmentStoreOp.VK_ATTACHMENT_STORE_OP_DONT_CARE,
            initialLayout=output.VkImageLayout.VK_IMAGE_LAYOUT_UNDEFINED,
            finalLayout=output.VkImageLayout.VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
        )
        color_ref = output.VkAttachmentReference(attachment=0, layout=output.VkImageLayout.VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
        subpass = output.VkSubpassDescription(
            pipelineBindPoint=output.VkPipelineBindPoint.VK_PIPELINE_BIND_POINT_GRAPHICS,
            colorAttachmentCount=1,
            pColorAttachments=pointer(color_ref),
        )
        dependency = output.VkSubpassDependency(
            srcSubpass=output.VK_SUBPASS_EXTERNAL,
            dstSubpass=0,
            srcStageMask=output.VkPipelineStageFlagBits.VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            dstStageMask=output.VkPipelineStageFlagBits.VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            srcAccessMask=0,
            dstAccessMask=output.VkAccessFlagBits.VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
        )

        create_info = output.VkRenderPassCreateInfo(
            attachmentCount=1, pAttachments=pointer(color_attachment),
            subpassCount=1, pSubpasses=pointer(subpass),
            dependencyCount=1, pDependencies=pointer(dependency),
        )
        render_pass = output.VkRenderPass()
        check(self.device.vkCreateRenderPass(create_info, None, byref(render_pass)), "vkCreateRenderPass")
        self.render_pass = render_pass

    def _load_shader_module(self, path):
        with open(path, "rb") as f:
            code = f.read()
        word_count = len(code) // 4
        buf = (c_uint32 * word_count).from_buffer_copy(code)   # SPIR-V is a uint32 word stream
        create_info = output.VkShaderModuleCreateInfo(codeSize=len(code), pCode=cast(buf, POINTER(c_uint32)))
        module = output.VkShaderModule()
        check(self.device.vkCreateShaderModule(create_info, None, byref(module)), "vkCreateShaderModule")
        return module, buf   # keep buf alive - see warning below

    def create_graphics_pipeline(self):
        vert_module, vert_buf = self._load_shader_module("shaders/triangle.vert.spv")
        frag_module, frag_buf = self._load_shader_module("shaders/triangle.frag.spv")

        vert_stage = output.VkPipelineShaderStageCreateInfo(stage=output.VkShaderStageFlagBits.VK_SHADER_STAGE_VERTEX_BIT, module=vert_module, pName=b"main")
        frag_stage = output.VkPipelineShaderStageCreateInfo(stage=output.VkShaderStageFlagBits.VK_SHADER_STAGE_FRAGMENT_BIT, module=frag_module, pName=b"main")
        stages = (output.VkPipelineShaderStageCreateInfo * 2)(vert_stage, frag_stage)

        vertex_input = output.VkPipelineVertexInputStateCreateInfo()   # no bindings - positions are hardcoded
        input_assembly = output.VkPipelineInputAssemblyStateCreateInfo(topology=output.VkPrimitiveTopology.VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST)

        viewport = output.VkViewport(x=0.0, y=0.0, width=float(self.swapchain_extent.width), height=float(self.swapchain_extent.height), minDepth=0.0, maxDepth=1.0)
        scissor = output.VkRect2D(offset=output.VkOffset2D(x=0, y=0), extent=self.swapchain_extent)
        viewport_state = output.VkPipelineViewportStateCreateInfo(viewportCount=1, pViewports=pointer(viewport), scissorCount=1, pScissors=pointer(scissor))

        rasterizer = output.VkPipelineRasterizationStateCreateInfo(
            polygonMode=output.VkPolygonMode.VK_POLYGON_MODE_FILL,
            cullMode=output.VkCullModeFlagBits.VK_CULL_MODE_BACK_BIT,
            frontFace=output.VkFrontFace.VK_FRONT_FACE_CLOCKWISE,
            lineWidth=1.0,
        )
        multisample = output.VkPipelineMultisampleStateCreateInfo(rasterizationSamples=output.VkSampleCountFlagBits.VK_SAMPLE_COUNT_1_BIT)

        color_blend_attachment = output.VkPipelineColorBlendAttachmentState(blendEnable=0, colorWriteMask=0xF)  # R|G|B|A
        color_blend = output.VkPipelineColorBlendStateCreateInfo(attachmentCount=1, pAttachments=pointer(color_blend_attachment))

        pipeline_layout = output.VkPipelineLayout()
        check(self.device.vkCreatePipelineLayout(output.VkPipelineLayoutCreateInfo(), None, byref(pipeline_layout)), "vkCreatePipelineLayout")
        self.pipeline_layout = pipeline_layout

        pipeline_info = output.VkGraphicsPipelineCreateInfo(
            stageCount=2, pStages=cast(stages, POINTER(output.VkPipelineShaderStageCreateInfo)),
            pVertexInputState=pointer(vertex_input),
            pInputAssemblyState=pointer(input_assembly),
            pViewportState=pointer(viewport_state),
            pRasterizationState=pointer(rasterizer),
            pMultisampleState=pointer(multisample),
            pColorBlendState=pointer(color_blend),
            layout=pipeline_layout,
            renderPass=self.render_pass,
            subpass=0,
        )
        pipeline = output.VkPipeline()
        check(self.device.vkCreateGraphicsPipelines(output.VkPipelineCache(0), 1, byref(pipeline_info), None, byref(pipeline)), "vkCreateGraphicsPipelines")
        self.pipeline = pipeline

        # shader modules aren't needed after pipeline creation
        self.device.vkDestroyShaderModule(vert_module, None)
        self.device.vkDestroyShaderModule(frag_module, None)

    def create_framebuffers(self):
        self.framebuffers = []
        for view in self.swapchain_image_views:
            create_info = output.VkFramebufferCreateInfo(
                renderPass=self.render_pass,
                attachmentCount=1,
                pAttachments=pointer(view),
                width=self.swapchain_extent.width,
                height=self.swapchain_extent.height,
                layers=1,
            )
            fb = output.VkFramebuffer()
            check(self.device.vkCreateFramebuffer(create_info, None, byref(fb)), "vkCreateFramebuffer")
            self.framebuffers.append(fb)

    def create_command_pool(self):
        create_info = output.VkCommandPoolCreateInfo(
            flags=output.VkCommandPoolCreateFlagBits.VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
            queueFamilyIndex=self.graphics_family,
        )
        pool = output.VkCommandPool()
        check(self.device.vkCreateCommandPool(create_info, None, byref(pool)), "vkCreateCommandPool")
        self.command_pool = pool

    def create_command_buffers(self):
        n = len(self.framebuffers)
        alloc_info = output.VkCommandBufferAllocateInfo(
            commandPool=self.command_pool,
            level=output.VkCommandBufferLevel.VK_COMMAND_BUFFER_LEVEL_PRIMARY,
            commandBufferCount=n,
        )
        buffers = (output.VkCommandBuffer * n)()
        check(self.device.vkAllocateCommandBuffers(alloc_info, buffers), "vkAllocateCommandBuffers")
        self.command_buffers = list(buffers)

        clear_value = output.VkClearValue(color=output.VkClearColorValue(float32=(0.01, 0.01, 0.02, 1.0)))

        for i, cmd in enumerate(self.command_buffers):
            check(self.device.vkBeginCommandBuffer(cmd, output.VkCommandBufferBeginInfo()), "vkBeginCommandBuffer")

            render_pass_info = output.VkRenderPassBeginInfo(
                renderPass=self.render_pass,
                framebuffer=self.framebuffers[i],
                renderArea=output.VkRect2D(offset=output.VkOffset2D(x=0, y=0), extent=self.swapchain_extent),
                clearValueCount=1,
                pClearValues=pointer(clear_value),
            )
            self.device.vkCmdBeginRenderPass(cmd, byref(render_pass_info), output.VkSubpassContents.VK_SUBPASS_CONTENTS_INLINE)
            self.device.vkCmdBindPipeline(cmd, output.VkPipelineBindPoint.VK_PIPELINE_BIND_POINT_GRAPHICS, self.pipeline)
            self.device.vkCmdDraw(cmd, 3, 1, 0, 0)
            self.device.vkCmdEndRenderPass(cmd)

            check(self.device.vkEndCommandBuffer(cmd), "vkEndCommandBuffer")

    def create_sync_objects(self):
        self.image_available_semaphores, self.in_flight_fences = [], []
        sem_info = output.VkSemaphoreCreateInfo()
        fence_info = output.VkFenceCreateInfo(flags=output.VkFenceCreateFlagBits.VK_FENCE_CREATE_SIGNALED_BIT)

        for _ in range(MAX_FRAMES_IN_FLIGHT):
            s1, f = output.VkSemaphore(), output.VkFence()
            check(self.device.vkCreateSemaphore(sem_info, None, byref(s1)), "vkCreateSemaphore")
            check(self.device.vkCreateFence(fence_info, None, byref(f)), "vkCreateFence")
            self.image_available_semaphores.append(s1)
            self.in_flight_fences.append(f)

        # one render-finished semaphore per swapchain image, not per frame-in-flight
        self.render_finished_semaphores = []
        for _ in range(len(self.swapchain_images)):
            s2 = output.VkSemaphore()
            check(self.device.vkCreateSemaphore(sem_info, None, byref(s2)), "vkCreateSemaphore")
            self.render_finished_semaphores.append(s2)

        self.current_frame = 0

    def draw_frame(self):
        fence = self.in_flight_fences[self.current_frame]
        self.device.vkWaitForFences(1, byref(fence), 1, UINT64_MAX)
        self.device.vkResetFences(1, byref(fence))

        image_index = c_uint32(0)
        self.device.vkAcquireNextImageKHR(
            self.swapchain, UINT64_MAX,
            self.image_available_semaphores[self.current_frame], output.VkFence(0), byref(image_index)
        )

        wait_semaphores = (output.VkSemaphore * 1)(self.image_available_semaphores[self.current_frame])
        signal_semaphores = (output.VkSemaphore * 1)(self.render_finished_semaphores[image_index.value])  # <-- changed
        wait_stages = (ctypes.c_uint32 * 1)(output.VkPipelineStageFlagBits.VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT)
        cmd_buffers = (output.VkCommandBuffer * 1)(self.command_buffers[image_index.value])

        submit_info = output.VkSubmitInfo(
            waitSemaphoreCount=1, pWaitSemaphores=cast(wait_semaphores, POINTER(output.VkSemaphore)),
            pWaitDstStageMask=cast(wait_stages, POINTER(ctypes.c_uint32)),
            commandBufferCount=1, pCommandBuffers=cast(cmd_buffers, POINTER(output.VkCommandBuffer)),
            signalSemaphoreCount=1, pSignalSemaphores=cast(signal_semaphores, POINTER(output.VkSemaphore)),
        )
        check(self.device.vkQueueSubmit(self.graphics_queue, 1, byref(submit_info), fence), "vkQueueSubmit")

        swapchains = (output.VkSwapchainKHR * 1)(self.swapchain)
        present_info = output.VkPresentInfoKHR(
            waitSemaphoreCount=1, pWaitSemaphores=cast(signal_semaphores, POINTER(output.VkSemaphore)),
            swapchainCount=1, pSwapchains=cast(swapchains, POINTER(output.VkSwapchainKHR)),
            pImageIndices=pointer(image_index),
        )
        self.device.vkQueuePresentKHR(self.present_queue, byref(present_info))

        self.current_frame = (self.current_frame + 1) % MAX_FRAMES_IN_FLIGHT

    def main_loop(self):
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.draw_frame()
        self.device.vkDeviceWaitIdle()   # don't destroy anything the GPU might still be using

    def run(self):
        self.init_window()
        self.create_instance()
        self.create_debug_messenger()
        self.create_surface()
        self.pick_physical_device()
        self.create_logical_device()
        self.create_swapchain()
        self.create_image_views()
        self.create_render_pass()
        self.create_graphics_pipeline()
        self.create_framebuffers()
        self.create_command_pool()
        self.create_command_buffers()
        self.create_sync_objects()
        try:
            self.main_loop()
        finally:
            self.cleanup()

    def cleanup(self):
        for s in self.image_available_semaphores: self.device.vkDestroySemaphore(s, None)
        for s in self.render_finished_semaphores: self.device.vkDestroySemaphore(s, None)
        for f in self.in_flight_fences: self.device.vkDestroyFence(f, None)
        self.device.vkDestroyCommandPool(self.command_pool, None)
        for fb in self.framebuffers: self.device.vkDestroyFramebuffer(fb, None)
        self.device.vkDestroyPipeline(self.pipeline, None)
        self.device.vkDestroyPipelineLayout(self.pipeline_layout, None)
        self.device.vkDestroyRenderPass(self.render_pass, None)
        for view in self.swapchain_image_views: self.device.vkDestroyImageView(view, None)
        self.device.vkDestroySwapchainKHR(self.swapchain, None)
        self.device.vkDestroyDevice(None)
        self.instance.vkDestroySurfaceKHR(self.surface, None)
        self.instance.vkDestroyDebugUtilsMessengerEXT(self.debug_messenger, None)
        self.instance.vkDestroyInstance(None)
        glfw.destroy_window(self.window)
        glfw.terminate()

App(name='Vulkan-Hello-Triangle').run()