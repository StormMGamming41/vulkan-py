
import glfw

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

    def initialize(self):

        self.init_window()

    def main_loop(self):

        while not glfw.window_should_close(self.window):
            glfw.poll_events()

    def cleanup(self):

        if self.window:
            glfw.destroy_window(self.window)
            self.window = None

        if self.glfw_initialized:
            glfw.terminate()
            self.glfw_initialized = False

    def run(self):

        try:
            self.initialize()
            self.main_loop()

        finally:
            self.cleanup()

if __name__ == "__main__":

    app = HelloTriangle("Hello Vulkan")
    app.run()

