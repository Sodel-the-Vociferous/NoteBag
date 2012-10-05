#!/usr/bin/python -B

# For getting the config file
import configparser
import os.path
from os.path import abspath, dirname, realpath, join as join_path
from sys import argv

# Widgets
from tkinter import Button, Entry, Frame, Label, Listbox, Scrollbar, Tk
# Constants
from tkinter import BOTH, BOTTOM, END, LEFT, N, S, W, E, X, Y

def read_config(filename):
    config_dir = abspath(realpath(dirname(argv[0])))
    config_path = join_path(config_dir, filename)

    config = configparser.ConfigParser()
    config.read(config_path)
    return config

class NoteBag:
    config = None
    notes = None

    # Class ("Static") Members
    CONFIG_FILENAME = "Notebag.ini"
    NOTES_FILENAME = "NoteFiles.pkl"

    def __init__(self, master):
        self.config = read_config(self.CONFIG_FILENAME)
        self.notes = {}

        ## High-level Layout
        input_frame = Frame(master)
        notes_frame = Frame(master)

        input_frame.pack(fill=X, padx=15)
        notes_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        ## Input Frame Setup
        note_name_label = Label(input_frame, text="Note Name: ")
        note_name_label.pack(side=LEFT)
        note_name_entry = Entry(input_frame)
        note_name_entry.pack(side=LEFT, fill=X, expand=True)
        search_note_button = Button(input_frame, text="Search")
        search_note_button.pack(side=LEFT)
        add_note_button = Button(input_frame, text="Add")
        add_note_button.pack(side=LEFT)

        ## Notes Frame Setup
        # List of existing notes
        existing_notes_label = Label(notes_frame, text="Existing Notes:")
        existing_notes_label.pack(anchor=W)
        all_notes = Listbox(notes_frame)
        all_notes.pack(side=LEFT, fill=BOTH, expand=True)
        notes_scrollbar = Scrollbar(notes_frame)
        notes_scrollbar.pack(side=LEFT, fill=Y)

        # Link scrollbar to list of notes
        all_notes.config(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.config(command=all_notes.yview)

        # Test data
        # TODO remove
        for i in range(1,50):
            all_notes.insert(END, str(i))

        ## Controls
        note_controls = Frame(notes_frame)
        note_controls.pack(side=LEFT, fill=Y)
        open_note_button = Button(note_controls, text="Open")
        open_note_button.pack(fill=X)
        delete_note_button = Button(note_controls, text="Delete")
        delete_note_button.pack(fill=X)


if __name__ == "__main__":
    root = Tk()
    notebag = NoteBag(root)
    root.mainloop()
