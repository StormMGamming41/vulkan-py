
from ctypes import byref, pointer, POINTER, cast, c_char_p

import glfw
import colorama
from colorama import Fore, just_fix_windows_console
from vulkan_py import *

def check(result, op):

    if result != VkResult.VK_SUCCESS:
        raise RuntimeError(f"Operation {op} failed execution | result: {result}")

class HelloTriangle:

    def __init__(self, name: str, res: tuple[int, int] = (800, 600), debug: bool = True):

        self.name = name
        self.res = res

        self.debug = debug

        colorama.init(autoreset=True)
        just_fix_windows_console()

        self.window = None
        self.glfw_initialized = False
    
    def _debug_callback(self, severity, msg_type, callback_data_ptr, user_data):

        data = callback_data_ptr.contents
        message = data.pMessage.decode(errors="ignore") if data.pMessage else "<no message>"
        
        col = Fore.BLUE

        if msg_type >= VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT:
            _tag = "PERF"
        elif msg_type >= VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT:
            _tag = "VALD"
        else:
            _tag = "GENR"

        if severity >= VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT:
            tag = "ERROR"
            col = Fore.RED
        elif severity >= VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT:
            tag = "WARN"
            col = Fore.YELLOW
        else:
            tag = "INFO"
        
        print(f"{col}[{_tag}:{tag}] {message} \33[0m")
        return 0 

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

        layers = []
        if self.debug: layers.append("VK_LAYER_KHRONOS_validation")
        lyr_bytes = [layer.encode("utf-8") for layer in layers]
        lyr_array = (c_char_p * len(lyr_bytes))(*lyr_bytes)

        required_exts = glfw.get_required_instance_extensions()
        exts_bytes = [ext.encode("utf-8") for ext in required_exts]
        if self.debug: exts_bytes.append(b"VK_EXT_debug_utils")
        ext_array = (c_char_p * len(exts_bytes))(*exts_bytes)

        create_info = VkInstanceCreateInfo(
            pApplicationInfo        = pointer(app_info),
            enabledExtensionCount   = len(exts_bytes),
            ppEnabledExtensionNames = cast(ext_array, POINTER(c_char_p)),
            enabledLayerCount       = len(lyr_bytes),
            ppEnabledLayerNames     = cast(lyr_array, POINTER(c_char_p))
        )

        raw_instance = VkInstance()
        check(vkCreateInstance(byref(create_info), None, byref(raw_instance)), "vkCreateInstance")
        self.raw_instance = raw_instance
        self.instance = Instance(raw_instance)

        print("Instance Created")

    def create_debug_messenger(self):

        self._debug_callback_fn = PFN_vkDebugUtilsMessengerCallbackEXT(self._debug_callback)

        create_info = VkDebugUtilsMessengerCreateInfoEXT(
            messageSeverity=(
                VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT
                | VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
                | VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT
            ),
            messageType=(
                VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT
                | VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT
                | VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT
            ),
            pfnUserCallback=self._debug_callback_fn,
        )

        messenger = VkDebugUtilsMessengerEXT()
        check(self.instance.vkCreateDebugUtilsMessengerEXT(create_info, None, byref(messenger)), "vkCreateDebugUtilsMessengerEXT")
        self.debug_messenger = messenger

        print("Created Debug Messenger")

        # callbackData = VkDebugUtilsMessengerCallbackDataEXT()
        # callbackData.pMessageIdName = b"VOLUNTARY_TRIGGER_TEST"
        # callbackData.messageIdNumber = 9999
        # callbackData.pMessage = b"This is a voluntary info message triggered manually by the application."
        
        # self.instance.vkSubmitDebugUtilsMessageEXT(
        #     VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT,
        #     VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT,
        #     byref(callbackData)
        # )
        # callbackData = VkDebugUtilsMessengerCallbackDataEXT()
        # callbackData.pMessageIdName = b"VOLUNTARY_TRIGGER_TEST"
        # callbackData.messageIdNumber = 9999
        # callbackData.pMessage = b"This is a voluntary waring message triggered manually by the application."
        
        # self.instance.vkSubmitDebugUtilsMessageEXT(
        #     VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT,
        #     VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT,
        #     byref(callbackData)
        # )
        # callbackData = VkDebugUtilsMessengerCallbackDataEXT()
        # callbackData.pMessageIdName = b"VOLUNTARY_TRIGGER_TEST"
        # callbackData.messageIdNumber = 9999
        # callbackData.pMessage = b"This is a voluntary error message triggered manually by the application."
        
        # self.instance.vkSubmitDebugUtilsMessageEXT(
        #     VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT,
        #     VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT,
        #     byref(callbackData)
        # )

    def initialize(self):

        self.init_window()
        self.create_instance()
        if self.debug: self.create_debug_messenger()

    def main_loop(self):

        while not glfw.window_should_close(self.window):
            glfw.poll_events()

    def cleanup(self):

        if self.debug: self.instance.vkDestroyDebugUtilsMessengerEXT(self.debug_messenger, None)

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

