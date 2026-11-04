# Instance

## Introduction

The Vulkan instance will be the first Vulkan object we create. It serves as the connection between our application and the Vulkan API. Vulkan provides us with a `VkInstance` handle, which we'll use to call dynamic commands. More on Vulkan commands in the next chapter.

## Creating an Instance

The first thing is to import the `vulkan-py` package in your file. We also need the `ctypes` library here, cuz the package doesn't contain a complete wrapper that covers everything, like the `vk::raii` wrapper for C++.

At the top of the file:

```python
from ctypes import byref, pointer, POINTER, cast, c_char_p, c_void_p, c_uint32, c_float # These are a few common things that we will be using

import glfw
import vulkan_py as vk

# rest of the things ...
```

You can also go with the second option below, but I recommend avoiding it if you have a low-end system, cuz your IDE might slow down due to it. You're free to use either of these two. I personally use the second one, and it's also used throughout this guide.

If you go with the first import, don't forget the `vk.` prefix when calling things from the package. With the second import, you can use them directly.

```python
from vulkan_py import *
```

Now, before we begin creating the instance, let's create a helper function. This will be pretty useful to us throughout the guide.

At the top of your file, after the imports, add this:

```python
def check(result, op):

    if result != VkResult.VK_SUCCESS:
        raise RuntimeError(f"Operation {op} failed execution | result : {result}") 
```

This will help us verify whether our command calls were successful or not.

Now let's begin creating the Vulkan instance.

Create a new function in the class called `create_instance`, after `init_window`:

```python
def init_window(self):

    # your code ...

def create_instance(self):

    # your code
```

This function will create our Vulkan instance.

Now, we need to fill the `VkApplicationInfo` structure:

```python
# your code

def create_instance(self):

    app_info = VkApplicationInfo(
        pApplicationName   = self.name.encode('utf-8'), # We need to pass strings in bytes form
        applicationVersion = 1,
        pEngineName        = b"No Engine", # Same here
        engineVersion      = 1,
        apiVersion         = (1 << 22) # This tells Vulkan that we'll use API version 1.0
    )
```

That's the structure filled in. Here's what each field does:

- `pApplicationName` tells the API the name of our application.
- `applicationVersion` tells the API the version of our application.
- `pEngineName` tells the API the name of the engine being used, which is `"No Engine"` in this case.
- `engineVersion` tells the API what version of the engine we are using.
- `apiVersion` is an important field. It tells Vulkan what version of the API we want to use.

Out of all these fields, `apiVersion` is the only important one that we actually need to provide a value for; all the other fields are optional. The `apiVersion` field can also be considered optional, cuz if left blank, Vulkan assumes version 1.0 by default.

The next step is to get the instance extensions required by GLFW. They are used by the API to create a surface through which it can present rendered frames on the GLFW window. We'll also fill in the `VkInstanceCreateInfo` structure, which is used for creating the instance.

Now, in `create_instance`, add this after filling the application info structure:

```python
def create_instance(self):

    # your code ...

    required_exts = glfw.get_required_instance_extensions()
    exts_bytes = [ext.encode("utf-8") for ext in required_exts]
    ext_array = (c_char_p * len(exts_bytes))(*exts_bytes)

    create_info = VkInstanceCreateInfo(
        pApplicationInfo        = pointer(app_info),
        enabledExtensionCount   = len(exts_bytes),
        ppEnabledExtensionNames = cast(ext_array, POINTER(c_char_p)),
        # enabledLayerCount       = 0
        # ppEnabledLayerNames     = 
    )
```

And that's the structure filled in. Now let's see what each field is for.

- `pApplicationInfo` takes a pointer to the `app_info` structure, which can later be referenced by the C API during instance creation.
- `enabledExtensionCount`, as its name suggests, tells Vulkan how many extensions we'll be enabling.
- `ppEnabledExtensionNames` takes an array of `c_char_p` objects containing the names of all the extensions we are enabling.
- `enabledLayerCount` and `ppEnabledLayerNames` are left ignored, cuz they are not necessary here. Layers are usually used during development for debugging and are often disabled when publishing.

We'll have a better look at using layers in a future chapter, where we'll use the `VK_LAYER_KHRONOS_validation` layer for setting up our debug messenger.

Now, the final part: creating the instance. Add the following code to the `create_instance` function:

```python
def create_instance(self):

    # your code ...

    raw_instance = VkInstance()
    check(vkCreateInstance(byref(create_info), None, byref(raw_instance)), "vkCreateInstance")
    self.raw_instance = raw_instance
    self.instance = Instance(raw_instance)

    print("Instance created")
```

And that's the instance creation done.

- Here, `raw_instance` is an empty `VkInstance` handle at the beginning.
- `vkCreateInstance` is the command that creates the instance and assigns a value pointing to it to the empty handle.
- The `Instance` object is a wrapper written in the `vulkan-py` package, which allows dynamic instance commands to be called like `self.instance.vk*`, while also skipping the first argument, which is, of course, the instance itself.

Now, update the `initialize` function to use this function and create a Vulkan instance:

```python
def initialize(self):

    self.init_window()
    self.create_instance()
```

And there you have your first Vulkan object created! But there's one more important thing before you run the file: every Vulkan object created needs to be destroyed after its purpose is fulfilled, and any memory allocated for them needs to be freed.

So, to destroy the Vulkan instance, add this to the cleanup function:

```python
def cleanup(self):

    self.instance.vkDestroyInstance(None)

    # your code ...
```

And that's it! Now you can run your application and verify instance creation with the print statement in `create_instance`.

>[!NOTE]
>If you have come this far, you might have noticed that the code written using this package closely resembles the actual C syntax for which Vulkan was originally made. This might make it easier to understand and translate examples and implementations written in C and C++, such as the original **Vulkan Tutorial** by **Khronos**.

---

Now is the right time to learn about Vulkan commands: what they are, how they are defined, and how they are called. So, in the [next chapter](2.1_commands.md), there will be a complete explanation of Vulkan commands.

---

| [← Previous](1_window.md) | [Next →](2.1_commands.md) |
|:---|---:|

---

## Files

- [`main.py`](code/main.py)

---