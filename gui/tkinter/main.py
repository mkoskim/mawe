import gui.tkinter as gui

root = gui.Tk()
root.title("mawesome")

def quit(event = None):
    print("Quit")
    global root
    root.destroy()


def run():
    root.bind("<Control-q>", quit)
    root.bind("<Alt-F4>", quit)

    st = gui.SceneGroupEditor(root)
    st.focus()

    root.mainloop()

