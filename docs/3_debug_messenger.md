# Debug Messenger

## Introduction

While developing an application using Vulkan, things can go wrong pretty easily. You might pass invalid arguments, use an unsupported feature, or make mistakes while managing Vulkan objects. And sometimes, figuring out what went wrong just by looking at your code can be quite frustrating.

This is where the **Debug Messenger** comes in.

The Vulkan Debug Messenger allows us to receive messages from Vulkan's validation layers and other enabled message sources. These messages can contain useful information about errors, warnings, and general events happening behind the scenes while our application is running.

In this chapter, we'll set up a debug messenger for our application so that we can catch these issues and get useful information about what's happening inside Vulkan, making development and debugging a whole lot easier.

## Some Preps. First

Before we begin with all the debug stuff, we need to make some changes (or say, a change) to our application class, as shown below:

```python
class HelloTriangle:

    def __init__(self, name: str, res: tuple[int, int] = (800, 600), debug: bool = True):

        self.name = name
        self.res = res

        self.debug = debug

        self.window = None
        self.glfw_initialized = False
```

As you may know, debug utilities, even outside of Vulkan, are generally meant to help us during the development process and are usually disabled before publishing. We need something to keep track of that, which is why we add a class variable `self.debug` to our application class.

Now, let's continue.

## Enabling Validation Layers

Enabling validation layers is a crucial part of this process, as `VK_LAYER_KHRONOS_validation`, a validation layer supplied with the **Vulkan SDK** that we talked about earlier, is the layer that analyses Vulkan API usage and generates debug messages that are really helpful to us (*cuz most of the time they're pretty straightforward*). There may be validation layers other than this one, but my knowledge about them (for now, ofc) ends here.

We enable this layer at the time of instance creation. So, we need to make some changes to the `create_instance` function too:

```python
def create_instance(self):

    # your code ...

    layers = []
    lyr_bytes = [layer.encode("utf-8") for layer in layers]
    if self.debug: lyr_bytes.append(b"VK_LAYER_KHRONOS_validation")
    lyr_array = (c_char_p * len(lyr_bytes))(*lyr_bytes)

    # your code ...

    create_info = VkInstanceCreateInfo(
        pApplicationInfo        = pointer(app_info),
        enabledExtensionCount   = len(exts_bytes),
        ppEnabledExtensionNames = cast(ext_array, POINTER(c_char_p)),
        enabledLayerCount       = len(lyr_bytes),
        ppEnabledLayerNames     = cast(lyr_array, POINTER(c_char_p))
    )

    # your code ...
```

> All of it is this way just to maintain consistency in the code.

Now, you might have some doubts after looking at this. Hold on to them; I'm explaining all of it:

- `layers = []` - We initialize with an empty layers list. This might not be empty if there are layers with specific features that your application requires to function, but that's a thing for the future.

- **The conditional statement** - By this time, you probably know why it's there, but still, for people who usually skip stuff, this is here so that when it's time for publishing, you can just set the `self.debug` variable to `False` and disable the debug utilities.

- `lyr_bytes` - You've seen something similar when preparing data for extensions. I missed this explanation there, but here it is. This is done cuz `vulkan-py` is just a C (*Vulkan was originally made for this*) representation of Vulkan in Python, and the underlying things still work with C, to which we can't pass Python strings, so they're converted to bytes.

- `lyr_array` - This is also similar to what we did with extensions. This is done cuz, just like Python strings, we can't directly pass a Python list to a C API either, so we convert it into an array of `ctypes` `c_char_p` objects.

- `cast` -

    >[!NOTE]
    >For this part, even I don't fully understand everything, so just remember that it works and use it. And please don't expect a proper explanation for this, cuz I also come from a pure Python background and know almost nothing about C/C++ other than the basics.

    Now, you might get an idea of why this is here by now. Even after converting the list of literals into an array, we still need to pass it as the pointer type expected by the API. So, at the time of assignment, we use the `cast` function to get a pointer of the required type.

- `enabledLayerCount` - The number of layers being enabled, as an integer.

- `ppEnabledLayerNames` - An array of names of the layers being enabled.

And that's it, now you have your validation layer(s) enabled.

## Enabling Debug Utils Extension

The validation layer is not the only part that needs to be added to instance creation. Enabling the `VK_EXT_debug_utils` extension is just as important as enabling the layers, cuz the layers do the job of analysing and generating messages, but those messages can't reach us on their own. This is where the `VkDebugUtilsMessengerEXT` Vulkan object comes in. It is made available to us through the `VK_EXT_debug_utils` extension.

So, again in `create_instance`:

```python
def create_instance(self):

    # your code ...

    # after the layers part
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

    # your code ...
```

And that's all. I don't think there's much to explain here. The only thing being done is adding the name of the `VK_EXT_debug_utils` extension to `exts_bytes` as bytes, under the debug condition.

## Creating the Debug Messenger

Hold your horses, we're almost done with this. This part is about creating the actual debug messenger object, which will inform us about what the API is doing, warn us about potential issues in our code, and report errors that we make while using the API. Let's get to it.

In your application class, create a new function named `create_debug_messenger`:

```python
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
```

Now, let's get to the meaning of all this code we just wrote:

- `self._debug_callback_fn` - This variable holds the callback function pointer that our debug messenger will use to send debug messages to us. `PFN_vkDebugUtilsMessengerCallbackEXT` takes a function that accepts all the arguments passed to it by the debug messenger. And yes, that means we have complete control over how to show or use the debug information. You can either just print it, save it to a log file, or even do both. We'll do this in the next section.

- **Filling in the `VkDebugUtilsMessengerCreateInfoEXT`** -

    This structure contains data about the messenger we will be creating, and we can specify the kinds of things it should report.

    - `messageSeverity` - This field takes the severity bits (defined in the API) for which the messenger should report. Here, we have selected Info, Warning, and Error bits, and their names tell you what they're for.

    - `messageType` - This field takes the message type bits (also defined in the API) for which the messenger should report. The Performance bit is for information about potential performance issues, the Validation bit is for information (usually useful) from validation layers, and the General bit is for general events happening in the background. Here, we use all three.

    - `pfnUserCallback` - This is the field that takes the callback function used by the messenger to deliver messages. It's through this callback that it gets access to our function, which we can customize almost however we want.

- The last part is the usual use of a command to create the object. You should've understood it by now. But just in case you don't, this might be the last time I explain it:

    - We define an empty `VkDebugUtilsMessengerEXT` handle.

    - Call an instance-level command, `vkCreateDebugUtilsMessengerEXT`, like this:

        ```python
        self.instance.vkCreateDebugUtilsMessengerEXT(create_info, None, byref(messenger))
        ```

        And pass in the `create_info` structure, `None` as the allocation callback, and the empty handle by reference.

    - We check the success code with the `check` helper function.

    - And finally, assign the handle with a valid value to a class variable.

And that's all of it. Now we're pretty close to completing this.

>[!TIP]
>If you are also going with all the options that I selected, adding color coding to your callabck function can be a pretty usefull thing, I've cover it in the next section.

## Debug Callback

In this section, we will be writing the function that our messenger will use to deliver debug messages to us. And remember, you can customize it almost **however you want it to be**. It just needs to accept all the arguments it gets from the debug messenger.

```python
def _debug_callback(self, severity, msg_type, callback_data_ptr, user_data):

    data = callback_data_ptr.contents
    message = data.pMessage.decode(errors="ignore") if data.pMessage else "<no message>"

    if msg_type & VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT:
        _tag = "PERF"
    elif msg_type & VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT:
        _tag = "VALD"
    else:
        _tag = "GENR"

    if severity & VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT:
        tag = "ERROR"
    elif severity & VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT:
        tag = "WARN"
    else:
        tag = "INFO"

    print(f"[{_tag}:{tag}] {message}")
    return 0
```

Now, let's understand what we made:

- At the beginning, in the function definition, `severity`, `msg_type`, `callback_data_ptr`, and `user_data` are all the arguments passed by the messenger to the function and must be accepted, though not everything might have a use currently. It might come in handy sometime in the future.

- Then, the next few lines are about unpacking the received data. As we pass strings as bytes, we also get strings as bytes back from the API (*it is what it is, but don't worry, I'm planning on adding a wrapper for this in the future*).

- The part after this is about getting a tag for the message type. This part is not necessary and can be skipped if you wish.

- This second-last part is about getting a tag for the severity of the message. This is important, as it helps us identify what kind of message we are receiving.

- This final part is the output. You can print it to the console like I did, log it into a file, or do both. And return a `0` value at the end. The `0` is crucial because it represents `VK_FALSE`, meaning we don't want to abort the Vulkan call that triggered the callback.

Now, all the Info messages that we'll encounter in the future might be too much for us to analyse. Large amounts of Info messages can easily hide the Warning and Error messages among them (*and none of us likes that*), so you could ignore adding the Info severity bit and the General message type bit, allowing you to look at only the important stuff.

Or, you could introduce color coding to it like I did. It's totally up to you what you wish to use.

To get colors working in our print statements, we need to make the following additions to our code.

At the top of the file:

```python
from ctypes import byref, pointer, POINTER, cast, c_char_p

import glfw
import colorama
from colorama import Fore, just_fix_windows_console
from vulkan_py import *
```

Then, in the `__init__` function of the application class:

```python
def __init__(self, name: str, res: tuple[int, int] = (800, 600), debug: bool = True):

    self.name = name
    self.res = res

    self.debug = debug

    colorama.init(autoreset=True)
    just_fix_windows_console()

    self.window = None
    self.glfw_initialized = False
```

And the final addition to our callback function, which finally makes it look like this:

```python
def _debug_callback(self, severity, msg_type, callback_data_ptr, user_data):

    data = callback_data_ptr.contents
    message = data.pMessage.decode(errors="ignore") if data.pMessage else "<no message>"

    col = Fore.BLUE

    if msg_type & VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT:
        _tag = "PERF"
    elif msg_type & VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT:
        _tag = "VALD"
    else:
        _tag = "GENR"

    if severity & VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT:
        tag = "ERROR"
        col = Fore.RED
    elif severity & VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT:
        tag = "WARN"
        col = Fore.YELLOW
    else:
        tag = "INFO"

    print(f"{col}[{_tag}:{tag}] {message} \33[0m")
    return 0
```

I'm not explaining the color-coding part, as you can find documentation on `colorama` on the web, at least enough to get you started.

Then, don't forget to add all of this to the `initialize` function:

```python
def initialize(self):

    self.init_window()
    self.create_instance()
    if self.debug: self.create_debug_messenger()
```

Now, just head to the next section, and we're pretty much done.

## Cleaning Up

I hope you do remember that every Vulkan object we create needs to be destroyed after its purpose is fulfilled.

Or you might end up in a funny situation where your messenger reports an error about itself:

```text
[VALD:ERROR] vkDestroyInstance(): VkInstance 0x1c341064100 has 1 leaked objects that have not been destroyed.
VkDebugUtilsMessengerEXT 0x10000000001
The Vulkan spec states: All child objects that were created with instance or with a VkPhysicalDevice retrieved from it, and that can be destroyed or freed, must have been destroyed or freed prior to destroying instance (https://docs.vulkan.org/spec/latest/chapters/initialization.html#VUID-vkDestroyInstance-instance-00629) 
```

>This might not be understandable right now but, no worries it's just an example.  
>*Why did I call that funny?* (Please don't mind these kinds of things, I just got sidetracked.)

So, finally, in the `cleanup` function:
```python
def cleanup(self):

    if self.debug: self.instance.vkDestroyDebugUtilsMessengerEXT(self.debug_messenger, None)

    self.instance.vkDestroyInstance(None)

    if self.window:
        glfw.destroy_window(self.window)
        self.window = None

    if self.glfw_initialized:
        glfw.terminate()
        self.glfw_initialized = False
```

And that's it! Now you have a debug messenger that may save you precious time that could otherwise be wasted searching through your entire code for one singular error.

---

We now have a working debug messenger that will help us catch Vulkan-related issues during development. From here on, whenever something goes wrong, we'll have a much easier time figuring out what happened instead of blindly searching through our code.

Now that we've got our debugging setup ready, it's time to move on to the next important part of Vulkan: physical devices. We'll learn how to enumerate the available GPUs, inspect their capabilities, and choose one for our application in the [next chapter](4_physical_device.md).

---

[← Previous](2.1_commands.md)

<!-- [Next →](4_physical_device.md) -->

---

## Links

- Colorama Docs - <https://www.geeksforgeeks.org/python/introduction-to-python-colorama/>

---

## Files

- [`main.py`](code/main.py)

---