#!/usr/bin/python -B

# For getting the config file
import configparser
import hashlib
import os.path
from os.path import abspath, dirname, realpath
import pickle
import string
from sys import argv

# Widgets
from tkinter import (Button, Entry, Frame, Label, Listbox,
                     Scrollbar, Tk, StringVar)
# Constants
from tkinter import BOTH, BOTTOM, END, LEFT, N, S, W, E, X, Y

def get_script_dir():
    return abspath(realpath(dirname(argv[0])))

def read_config(filename):
    config_dir = get_script_dir()
    config_path = os.path.join(config_dir, filename)

    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def notes_checksum(notes):
    digest = hashlib.sha1()
    for key in notes:
        digest.update(key)
        digest.update(notes[key])
    return digest.hexdigest()

def save_notes_list(notes, file_obj):
    pickle.dump(notes_checksum(notes), file_obj)
    pickle.dump(notes, file_obj)

def read_notes_list(file_obj):
    saved_checksum = pickle.load(file_obj)
    notes = pickle.load(file_obj)
    loaded_checksum = notes_checksum(notes)

    if loaded_checksum != saved_checksum:
        raise ValueError("The list of notes has been corrupted")
    return notes


class NoteBag:
    config = None
    notes = None

    # Config Options
    notes_filename = None
    notes_dir = None

    # GUI Elements
    note_name_action_strvar = None
    note_name_entry_strvar = None
    note_name_entry = None
    note_names_label_strvar = None
    note_names_listbox = None

    # Class ("Static") Members
    CONFIG_FILENAME = "NoteBag.ini"

    ## Back-End Methods
    def load_config(self, filename):
        config = self.config = read_config(self.CONFIG_FILENAME)
        self.notes_filename = config.get("NoteBag", "Notes List File")
        self.notes_dir = config.get("NoteBag", "Notes Directory")

    def load_notes(self, filename):
        notes_list_dir = get_script_dir()
        notes_list_file = os.path.join(notes_list_dir, filename)

        # TODO handle exceptions
        if not os.path.isfile(notes_list_file):
            self.notes = {}
            # TEST DATA
            # TODO remove
            self.notes = {"Foo": "bar.rtf"}
        else:
            with open(notes_list_file) as f:
                self.notes = read_notes_list(f)

    def get_entered_note_name(self):
        return self.note_name_entry.get().strip()

    def get_note_name_key(self, note_name):
        note_names = self.notes.keys()
        note_names = map(lambda s: s.lower(), note_names)
        for existing_note_name in note_names:
            if note_name.lower() == existing_note_name:
                print("Wee!")
                return existing_note_name
        return None

    def update_note_names_list(self, search_str=""):
        note_names = self.notes.keys()

        # Remove strings that don't match
        if search_str:
            def string_matches_search(s):
                return search_str.lower() in s.lower()
            note_names = filter(string_matches_search, note_names)

        # Sort Alphabetically
        note_names = sorted(note_names, key=lambda s: s.lower)

        # Update the note name listbox
        note_names_listbox = self.note_names_listbox
        note_names_listbox.delete(0, END)
        for note_name in note_names:
            note_names_listbox.insert(END, note_name)

        # Update the note name list label
        if search_str:
            s = "All Note Names Containing '{0}':".format(search_str)
        else:
            s = "All Existing Notes:"
        self.note_names_label_strvar.set(s)

    ## GUI Callbacks
    def note_name_action_callback(self, *_args, **_kwargs):
        note_name = self.get_entered_note_name()
        key = self.get_note_name_key(note_name)
        if key:
            note_filename = self.notes[key]
            # TODO
            #note_file = os.path.join(self.notes_dir, note_filename)
            #open_note(note_file)
        else:
            # TODO ask the use if they really want to add a note,
            # popup a small note setup dialog, and add the note.
            pass
        print("Bar")

    def note_name_entry_changed(self, *_args, **_kwargs):
        entered_note_name = self.get_entered_note_name()
        self.update_note_names_list(search_str=entered_note_name)

        if self.get_note_name_key(entered_note_name):
            self.note_name_action_strvar.set("Open")
        else:
            self.note_name_action_strvar.set("Add")

    def clear_note_name_entry(self):
        self.note_name_entry.delete(0, END)

    ## Main Code
    def __init__(self, master):
        ## High-level Layout
        input_frame = Frame(master)
        notes_frame = Frame(master)

        input_frame.pack(fill=X, padx=15)
        notes_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        ## Input Frame Setup
        note_name_label = Label(input_frame, text="Note Name: ")
        note_name_label.pack(side=LEFT)

        self.note_name_entry_strvar = StringVar()
        self.note_name_entry_strvar.set("")
        self.note_name_entry_strvar.trace("w", self.note_name_entry_changed)
        self.note_name_entry = Entry(input_frame,
                                     textvariable=self.note_name_entry_strvar)
        self.note_name_entry.pack(side=LEFT, fill=X, expand=True)
        self.note_name_entry.bind("<Return>", self.note_name_action_callback)
        self.note_name_entry.bind("<KP_Enter>", self.note_name_action_callback)

        self.note_name_action_strvar = StringVar()
        note_name_action_strvar = self.note_name_action_strvar
        note_name_action_strvar.set("Add")
        note_name_action_button = Button(input_frame,
                                         textvar=note_name_action_strvar,
                                         command=self.note_name_action_callback)
        note_name_action_button.pack(side=LEFT)
        clear_note_name_button = Button(input_frame, text="Clear",
                                        command=self.clear_note_name_entry)
        clear_note_name_button.pack(side=LEFT)

        ## Notes Frame Setup
        # List of existing notes
        self.note_names_label_strvar = StringVar()
        note_names_label_strvar = self.note_names_label_strvar
        note_names_label = Label(notes_frame,
                                 textvar=note_names_label_strvar)
        note_names_label.pack(anchor=W)

        note_names_listbox = self.note_names_listbox = Listbox(notes_frame)
        note_names_listbox.pack(side=LEFT, fill=BOTH, expand=True)

        notes_scrollbar = Scrollbar(notes_frame)
        notes_scrollbar.pack(side=LEFT, fill=Y)

        # Link scrollbar to list of notes
        note_names_listbox.config(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.config(command=note_names_listbox.yview)

        ## Controls
        note_controls = Frame(notes_frame)
        note_controls.pack(side=LEFT, fill=Y)

        open_note_button = Button(note_controls, text="Open")
        open_note_button.pack(fill=X)

        delete_note_button = Button(note_controls, text="Delete")
        delete_note_button.pack(fill=X)

        ## Final Initialization
        self.load_config(self.CONFIG_FILENAME)
        self.load_notes(self.notes_filename)
        self.update_note_names_list()

if __name__ == "__main__":
    root = Tk()
    notebag = NoteBag(root)
    root.mainloop()
