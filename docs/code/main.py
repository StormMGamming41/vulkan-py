
from ctypes import byref, pointer, POINTER, cast, c_char_p

import glfw
from vulkan_py import *

def check(result, op):

    if result != VkResult.VK_SUCCESS:
        raise RuntimeError(f"Operation {op} failed execution | result: {result}")

class HelloTriangle:

    def __init__(self, name: str, res: tuple[int, int] = (800, 600)):

        self.name = name
        self.res = res
        self.window = None
        self.glfw_initialized = False
    
    def init_window(self):

        if not glfw.init():
            raise RuntimeError("glfw.init() failed")

        self.glfw_initialized = True

        glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)

        self.window = glfw.create_window(
            self.res[0],
            self.res[1],
            self.name,
            None,
            None
        )

        if not self.window:
            raise RuntimeError("glfw.create_window() failed")

    def create_instance(self):

        app_info = VkApplicationInfo(
            pApplicationName   = self.name.encode('utf-8'), # We need to pass strings in bytes form
            applicationVersion = 1,
            pEngineName        = b"No Engine", # Same here
            engineVersion      = 1,
            apiVersion         = (1 << 22) # This tells vulkan that we'll use api version 1.0
        )

        required_exts = glfw.get_required_instance_extensions()
        exts_bytes = [ext.encode("utf-8") for ext in required_exts]
        ext_array = (c_char_p * len(exts_bytes))(*exts_bytes)

        create_info = VkInstanceCreateInfo(
            pApplicationInfo        = pointer(app_info),
            enabledExtensionCount   = len(exts_bytes),
            ppEnabledExtensionNames = cast(ext_array, POINTER(c_char_p)),
            enabledLayerCount       = 0
        )

        raw_instance = VkInstance()
        check(vkCreateInstance(byref(create_info), None, byref(raw_instance)), "vkCreateInstance")
        self.raw_instance = raw_instance
        self.instance = Instance(raw_instance)

        print("Instance Created")

    def initialize(self):

        self.init_window()
        self.create_instance()

    def main_loop(self):

        while not glfw.window_should_close(self.window):
            glfw.poll_events()

    def cleanup(self):

        if self.instance:
            self.instance.vkDestroyInstance(None)

        if self.window:
            glfw.destroy_window(self.window)
            self.window = None

        if self.glfw_initialized:
            glfw.terminate()
            self.glfw_initialized = False

    def run(self):

        self.initialize()
        self.main_loop()

        self.cleanup()

if __name__ == "__main__":

    app = HelloTriangle("Hello Vulkan")
    app.run()

