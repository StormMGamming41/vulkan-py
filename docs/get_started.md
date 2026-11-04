# Getting Started

## Index

1. [Window](1_window.md)
2. [Instance](2_instance.md)  
  2.1. [Vulkan Commands](2.1_commands.md)


---

> [!NOTE]
> This is a rewrite of the previous guide due to some mistakes and inconsistencies in the earlier version.
>
> If you encounter any difficulties while following this guide, I apologize in advance.
>
> Special thanks to @Evolution0 for bringing these issues to my attention.

## Introduction

**Vulkan-Py** is a Python binding for the [Vulkan® API](https://www.vulkan.org/), designed to make Vulkan accessible to Python developers while retaining the flexibility and control that Vulkan provides.

The goal of this project is to bring Vulkan's capabilities to Python without hiding the underlying API behind excessive abstractions. The binding aims to stay close to Vulkan itself, allowing developers to work with familiar Vulkan concepts, structures, handles and functions directly from Python.

This guide will walk you through using Vulkan-Py, starting with the initial setup and gradually moving towards more complex concepts and practical implementations. It follows the official [Khronos Vulkan Tutorial](https://docs.vulkan.org/tutorial/latest/00_Introduction.html), with examples adapted to Python and this binding.

## Requirements

Before getting started with Vulkan-Py, there are a few things you'll need to have set up on your system.

- **Python** – I'd recommend using *Python 3.12*, as that's the version I used during development. However, you're free to use any other version, provided it's compatible with the version of Vulkan-Py you're installing.

  - [Download Python](https://www.python.org/downloads/)

- **Vulkan SDK** – You'll need the official [Vulkan SDK by LunarG](https://vulkan.lunarg.com/sdk/home) for development. It provides useful tools, validation layers and other resources that make working with Vulkan considerably easier.

  - [Vulkan SDK Installation Guide](https://docs.vulkan.org/guide/latest/loader.html)

- **Vulkan-capable GPU and drivers** – You'll need a GPU with Vulkan support and the appropriate graphics drivers installed. Make sure your GPU and drivers support the Vulkan version you intend to use.

  - [Vulkan Hardware Database](https://vulkan.gpuinfo.org/)

- **Vulkan-Py** – This is the package this guide is all about, and we'll be building some cool stuff with it!

  Installing it is pretty straightforward. You'll just need Python and pip installed on your system. Open PowerShell, Command Prompt, or your IDE's terminal and run:

  ```bash
  pip install vulkan-py
  ```

  And that's pretty much it!

- **An IDE or Text Editor** – This one's optional. Any text editor that supports Python will work, but I'd recommend using an IDE as it provides useful tools and features that make development easier.

  I personally use [Visual Studio Code](https://code.visualstudio.com/), but feel free to use whichever editor you're comfortable with.

## Verifying Your Installation

Before moving on, let's make sure everything is properly installed and Vulkan is accessible on your system.

We'll perform few simple checks:

### 1. Checking Vulkan-Py

First, let's verify that Python can successfully import the package.

Open your terminal and run:

```bash
python -c "import vulkan_py; print('Vulkan-Py imported successfully!')"
```

If everything is set up correctly, you should see:

```text
Vulkan-Py imported successfully!
```

If you encounter an `ImportError` or `ModuleNotFoundError`, make sure you've installed the package in the Python environment you're currently using.

### 2. Checking Vulkan Runtime

Next, we need to verify that your system can actually communicate with a Vulkan-capable GPU.

Fortunately, the Vulkan SDK provides a utility called `vulkaninfo`, which gathers information about your Vulkan installation and available devices.

Open your terminal and execute:

```bash
vulkaninfo --summary
```

On Windows, if the command isn't available, you can try running the SDK's version instead:

```powershell
vulkaninfoSDK --summary
```

If everything is working correctly, you should see information about your Vulkan instance and available physical devices, including their supported Vulkan API versions.

For example, you should be able to identify your GPU under the device summary.

> [!TIP]
> You can run `vulkaninfo` without any arguments to get more detailed information about your Vulkan installation, including supported extensions, device properties and available layers.

### 3. Running the Vulkan Cube

Now for something a little more interesting!

Try running:

```bash
vkcube
```

### 4. All Set!

If both checks completed successfully, you're good to go!

Your Python environment can import Vulkan-Py, and your system has a working Vulkan runtime with a compatible device.

We can finally move on to the interesting part: writing some actual Vulkan code!

---

[Next →](1_window.md)

---