

# Window

## Introduction

The ending of the setup guide might have been a bit misleading, but there's one more thing we need to take care of before working with Vulkan.

We'll set that up in this chapter. The actual Vulkan concepts begin in the next one.

For making a Vulkan application (or any graphics-related application in general), the first thing we need to do is set up a window. In this example, we'll be using the `glfw` library to handle the windowing part of the application.

## Installation

This installation is also pretty straightforward and similar to the way we installed the binding package.

Run the following command in your terminal:

```bash
pip install glfw
```

That's all! Now let's write some actual code.

## Let's Begin

First, let's define a basic structure for our application. We'll be adding more functionality to this class as we progress through the tutorial.

```python
import glfw


class HelloTriangle:

    def __init__(self, name: str, res: tuple[int, int] = (800, 600)):

        self.name = name
        self.res = res
        self.window = None
        self.glfw_initialized = False

    def initialize(self):

        pass

    def main_loop(self):

        pass

    def cleanup(self):

        pass
```

Nothing complicated here. We're simply defining a class that will handle the initialization, main loop and cleanup of our application.

## Creating the Window

Now comes the actual window creation part. Add the following function to our class:

```python
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
```

Let's go through what's happening here:

- `glfw.init()` initializes the GLFW library. We need to do this before using its windowing functionality.
- `glfw.window_hint()` allows us to specify certain properties for the window we're about to create.
- `glfw.CLIENT_API` specifies which graphics API GLFW should use to create the window.
- `glfw.NO_API` tells GLFW not to create an OpenGL or OpenGL ES context. Since we're using Vulkan, we don't need one.
- `glfw.RESIZABLE` specifies whether the window can be resized.
- `glfw.FALSE` tells GLFW to disable resizing.
- `glfw.create_window()` finally creates our window using the properties we've specified.

You might have noticed that we're passing `None` twice to `glfw.create_window()`. These arguments are for the monitor and shared window respectively. We don't need either of them for now.

## Putting Everything Together

Now that we have our window creation function, let's put it to use.

In `initialize()`, call our newly created function:

```python
def initialize(self):

    self.init_window()
```

Next, let's implement our main loop:

```python
def main_loop(self):

    while not glfw.window_should_close(self.window):
        glfw.poll_events()
```

`glfw.window_should_close()` checks whether the window has received a close request.

`glfw.poll_events()` processes pending window events, such as keyboard input, mouse input and window close requests.

For now, we're not doing anything with these events. We'll get to that later.

Finally, let's implement the cleanup function:

```python
def cleanup(self):

    if self.window:
        glfw.destroy_window(self.window)
        self.window = None

    if self.glfw_initialized:
        glfw.terminate()
        self.glfw_initialized = False
```

We use `glfw.destroy_window()` to destroy our window and `glfw.terminate()` to shut down GLFW and release its resources.

## Running the Application

We're almost done! We just need a way to bring everything together.

Add the following function to our class:

```python
def run(self):

    try:
        self.initialize()
        self.main_loop()

    finally:
        self.cleanup()
```

This ensures that our cleanup function is called even if an error occurs during initialization or while running the application.

Now, outside the class, add:

```python
if __name__ == "__main__":

    app = HelloTriangle("Hello Vulkan")
    app.run()
```

And that's it!

Run your Python file, and you should see a blank window titled **Hello Vulkan**.

---

In the next chapter, we'll finally be creating our first **Vulkan object**: a `VkInstance` object, which serves as the connection between our application and the Vulkan API.

---

[← Previous](get_started.md)

[Next →](2_instance.md)

---

## Files

- [`main.py`](code/main.py)

---
