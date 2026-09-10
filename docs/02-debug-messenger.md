# 2. Debug Messenger

[← Back to index](README.md) · Previous: [Instance Creation](01-instance.md) · Next: [Window Surface →](03-surface.md)

With `VK_EXT_debug_utils` and the validation layer enabled on the instance (Chapter 1), the next step is telling Vulkan *what to do* with the messages that layer produces — that's the debug messenger's job.

## The callback

Vulkan calls this function directly whenever validation has something to say. It hands you a severity, a message type, and a struct containing the actual text:

```python
def debug_callback(self, severity, msg_type, callback_data_ptr, user_data):
    data = callback_data_ptr.contents
    message = data.pMessage.decode(errors="ignore") if data.pMessage else "<no message>"
    col = "\033[34m"

    if severity >= VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT:
        tag = "ERROR"
        col = "\033[31m"
    elif severity >= VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT:
        tag = "WARN"
        col = "\033[38;5;208m"
    elif severity >= VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT:
        tag = "INFO"
    else:
        tag = "VERB"

    print(f"{col}[validation:{tag}] {message}" + "\033[0m")
    return VK_FALSE
```

Returning `VK_FALSE` tells Vulkan "don't abort the call that triggered this message" — that's what you want almost always; returning `VK_TRUE` is reserved for testing the validation layers themselves.

## Wrapping it as a Vulkan function pointer

Vulkan needs an actual C function pointer, not a bare Python method — `vulkan_py` gives you `PFN_vkDebugUtilsMessengerCallbackEXT` for exactly this:

```python
self.callback_fn = PFN_vkDebugUtilsMessengerCallbackEXT(self.debug_callback)
```

> Keep a reference to `callback_fn` for the lifetime of the messenger (e.g. as `self.callback_fn`) — if it gets garbage collected, Vulkan will be calling into freed memory.

## Creating the messenger

Pick which severities and categories of message you care about, then create the messenger through the instance:

```python
create_info = VkDebugUtilsMessengerCreateInfoEXT(
    messageSeverity=(
        VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT
        | VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT
        | VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
        | VkDebugUtilsMessageSeverityFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT
    ),
    messageType=(
        VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT
        | VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT
        | VkDebugUtilsMessageTypeFlagBitsEXT.VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT
    ),
    pfnUserCallback=self.callback_fn
)

messenger = VkDebugUtilsMessengerEXT()
check(
    self.instance.vkCreateDebugUtilsMessengerEXT(create_info, None, byref(messenger)),
    "vkCreateDebugUtilsMessengerEXT"
)
self.debug_messenger = messenger
```

Notice this call goes through `self.instance` — the `Instance` wrapper from Chapter 1 — rather than as a loose function like `vkCreateInstance` was. Every extension function that's loaded per-instance (as opposed to global functions like instance creation itself) dispatches this way.

> **Why bother color-coding the callback?** `VERBOSE` and `INFO` severities are included above, and they're the two easiest to enable and immediately regret — Vulkan is chatty at those levels, and the flood of routine noise makes it easy to miss the one `WARN` or `ERROR` line that actually matters. Color-coding each severity (and specifically making errors loud/red) means a real problem still jumps out at you even when it's buried in pages of verbose/info logging, instead of relying on you to read every line.

Skip this whole chapter in release builds — it's gated behind `DEBUG_MODE` since validation has real runtime cost and end users don't need to see it.

[← Back to index](README.md) · Previous: [Instance Creation](01-instance.md) · Next: [Window Surface →](03-surface.md)