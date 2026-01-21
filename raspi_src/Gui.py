"""
Docstring for raspi_src.Gui

Gui
Jack

"""

import tkinter

class Gui:
    def __init__(self):
        self.root = tkinter.Tk()

    def open(self) -> None:
        # init stuff
        self.root.title("Debug Gui")
        self.root.geometry('320x200')
        self._initGeometry()
        self.root.mainloop()


    def _initGeometry(self):
        pass

if __name__ == "__main__":
    gui = Gui()
    gui.open()