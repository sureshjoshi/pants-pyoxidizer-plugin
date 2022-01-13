import kivy
from kivy.app import App
from kivy.uix.label import Label

kivy.require("2.0.0")


class MyFirstKivyApp(App):
    def build(self):
        return Label(text="Hello World !")


def main():
    MyFirstKivyApp().run()


if __name__ == "__main__":
    print("Launching HelloKivy from __main__")
    main()
