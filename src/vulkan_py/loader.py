
# Copyright (C) 2026 StormMGamming41
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import platform
from ctypes import *
from .handles import VkInstance
from .commands import PFN_vkGetInstanceProcAddr, PFN_vkCreateInstance, PFN_vkGetDeviceProcAddr, PFN_vkEnumerateInstanceExtensionProperties, PFN_vkEnumerateInstanceLayerProperties

def _load_vulkan_library():
    system = platform.system()
    try:
        if system == "Windows":
            return WinDLL("vulkan-1.dll")
        elif system == "Linux":
            return CDLL("libvulkan.so.1")
        elif system == "Darwin":
            return CDLL("libvulkan.dylib")
        raise RuntimeError(f"Unsupported platform: {system}")
    except OSError as e:
        raise RuntimeError(
            "Could not load the Vulkan runtime library. "
            "Make sure Vulkan-capable GPU drivers are installed."
        ) from e

_lib = _load_vulkan_library()

vkGetInstanceProcAddr = _lib.vkGetInstanceProcAddr
vkGetInstanceProcAddr.restype = PFN_vkGetInstanceProcAddr._restype_
vkGetInstanceProcAddr.argtypes = PFN_vkGetInstanceProcAddr._argtypes_

vkCreateInstance = _lib.vkCreateInstance
vkCreateInstance.restype = PFN_vkCreateInstance._restype_
vkCreateInstance.argtypes = PFN_vkCreateInstance._argtypes_

vkGetDeviceProcAddr = _lib.vkGetDeviceProcAddr
vkGetDeviceProcAddr.restype = PFN_vkGetDeviceProcAddr._restype_
vkGetDeviceProcAddr.argtypes = PFN_vkGetDeviceProcAddr._argtypes_

vkEnumerateInstanceExtensionProperties = _lib.vkEnumerateInstanceExtensionProperties
vkEnumerateInstanceExtensionProperties.restype = PFN_vkEnumerateInstanceExtensionProperties._restype_
vkEnumerateInstanceExtensionProperties.argtypes = PFN_vkEnumerateInstanceExtensionProperties._argtypes_

vkEnumerateInstanceLayerProperties = _lib.vkEnumerateInstanceLayerProperties
vkEnumerateInstanceLayerProperties.restype = PFN_vkEnumerateInstanceLayerProperties._restype_
vkEnumerateInstanceLayerProperties.argtypes = PFN_vkEnumerateInstanceLayerProperties._argtypes_
