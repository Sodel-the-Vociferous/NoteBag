#!/usr/bin/python -B

CONFIG_FILENAME = "NoteBag.ini"

import hashlib
from helpers import get_called_script_dir, read_config, save_config
import os
import pickle
import string
import subprocess
import sys # for platform

# Compensate for Python 2.x and 3.x having different module names, and
# no good way to make the same imports work on both.
try:
    # Widgets
    from tkinter import (Button, Entry, Frame, Label, Listbox,
                         Scrollbar, Tk, StringVar)
    from tkinter import messagebox, filedialog
    # Constants
    from tkinter import BOTH, BOTTOM, END, LEFT, N, S, W, E, X, Y
except ImportError:
    # Widgets
    from Tkinter import (Button, Entry, Frame, Label, Listbox,
                         Scrollbar, Tk, StringVar)
    import tkMessageBox as messagebox, tkFileDialog as filedialog
    # Constants
    from Tkinter import BOTH, BOTTOM, END, LEFT, N, S, W, E, X, Y

## GLOBAL VARS
# A common-denominator between Python 2.x and 3.x
PICKLE_PROTOCOL = 2


def notes_checksum(notes):
    """
    Return the hash digest of a list of notes as a string.
    """

    digest = hashlib.sha1()
    for note_name in notes:
        note_name_bytes = note_name.encode('utf-8')
        filename_bytes = notes[note_name].encode('utf-8')
        digest.update(note_name_bytes)
        digest.update(filename_bytes)
    return digest.hexdigest()

def save_notes_list(notes, file_path):
    """
    Write a list of notes out to a file. Also write a checksum of the
    notes list, so read_notes_list() can validate what it reads.
    """

    with open(file_path, "wb") as f:
        pickle.dump(notes_checksum(notes), f, PICKLE_PROTOCOL)
        pickle.dump(notes, f, PICKLE_PROTOCOL)

def read_notes_list(file_path):
    """
    Read a list of notes back from a file.

    If the checksum from the file doesn't match the checksum of all of
    the notes that were read from it, raise a ValueError.
    """

    with open(file_path, "rb") as f:
        saved_checksum = pickle.load(f)
        notes = pickle.load(f)

    loaded_checksum = notes_checksum(notes)
    if loaded_checksum != saved_checksum:
        raise ValueError("The list of notes has been corrupted")
    return notes

def sanitize_note_name(note_name):
    """
    Very conservatively remove any characters from a note name that
    might not play nice with a filesystem.
    """

    note_name = note_name.strip()
    def okay_filename_char(c):
        return c.lower() in "abcdefghijklmnopqrstuvwxyz .-_'"
    return "".join(list(filter(okay_filename_char, tuple(note_name))))

def create_skeleton_note(note_name, note_path, template_file_path):
    """
    Create a skeleton note document, containing just the note's name.
    """

    with open(template_file_path) as tf:
        template_lines = tf.readlines()
    skeleton_lines = [line.replace("%(NOTE NAME)%", note_name)
                      for line in template_lines]
    skeleton_lines = [line.encode('utf-8') for line in skeleton_lines]

    with open(note_path, 'wb') as f:
        for line in skeleton_lines:
            f.write(line)

def open_note(note_path, document_editor=None):
    """
    Open a note for editing with with a program.

    Use the document_editor arg if available; otherwise, use a command
    appropriate to the operating system that will open the default
    program for the file type.
    """

    # Choose the document editor and Popen() settings based on the
    # operating system.
    creationflags = 0
    if document_editor:
        program = document_editor
    elif os.name.lower() == "nt":
        # I'm not using the win32process library, so I can't just
        # import DETACHED_PROCESS from there.
        DETACHED_PROCESS = 0x8
        creationflags |= DETACHED_PROCESS
        program = "start"
    elif sys.platform.lower() == "darwin":
        # Mac OSX
        program = "open"
    elif os.name.lower() == "posix":
        program = "xdg-open"
    else:
        messagebox.showerror("OS Not Supported",
                             "Your operating system is not supported")
        return

    subprocess.Popen([program, note_path], creationflags=creationflags,
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)


class NoteBag:
    config = None
    notes = None

    # Config Options
    notes_filename = None
    notes_dir = None
    note_template_filename = None
    document_editor = None

    # GUI Elements
    note_name_action_strvar = None
    note_name_entry_strvar = None
    note_name_entry = None
    note_names_label_strvar = None
    note_names_listbox = None

    ## Back-End Methods
    def notes_list_path(self):
        """
        Return the path to the notes list file.
        """

        return os.path.join(self.notes_dir, self.notes_list_filename)

    def template_note_path(self):
        """
        Return the path to the template note file.
        """

        return os.path.join(get_called_script_dir(), self.note_template_filename)

    def note_path(self, note_name):
        """
        Return the path to an existing note document.
        """

        note_filename = self.notes[note_name]
        note_path = os.path.join(self.notes_dir, note_filename)
        return note_path

    def get_listbox_selected_note_name(self):
        """
        Return the note name that is selected in the listbox; if there
        is no selection, return None.
        """

        selections = self.note_names_listbox.curselection()
        if not selections:
            return None
        selection = selections[0]
        note_name = self.note_names_listbox.get(selection)
        return note_name

    def load_config(self):
        """
        Load a config file, and use it to set config options.
        """

        config = self.config = read_config(CONFIG_FILENAME)
        self.notes_list_filename = config.get("NoteBag", "Notes List File")
        self.notes_dir = config.get("NoteBag", "Notes Directory")
        self.note_template_filename = config.get("NoteBag", "Note Template Filename")
        self.document_editor = config.get("NoteBag", "Document Editor")

    def load_notes_list(self):
        """
        Load the list of notes.
        """

        # TODO handle exceptions
        notes_list_path = self.notes_list_path()
        if not os.path.isfile(notes_list_path):
            self.notes = {}
        else:
            self.notes = read_notes_list(notes_list_path)

    def save_notes_list(self):
        """
        Save the list of notes.
        """

        save_notes_list(self.notes, self.notes_list_path())

    def get_entered_note_name(self):
        """
        Get the text that has been entered into the "Note Name" text
        entry box, with all leading and trailing spaces stripped off.
        """

        return self.note_name_entry.get().strip("\t ")

    def get_note_name_key(self, note_name):
        note_names = self.notes.keys()
        for existing_note_name in note_names:
            if note_name.lower() == existing_note_name.lower():
                return existing_note_name
        return None

    def add_note(self, note_name, note_filename=None):
        """
        Add a note document, and save the list of notes.
        """

        note_path = os.path.join(self.notes_dir, note_filename)
        create_skeleton_note(note_name, note_path, self.template_note_path())

        self.notes[note_name] = note_filename
        self.save_notes_list()

    def update_note_names_list(self):
        """
        Update the listbox of the existing notes, and the list's
        label. If there is any text entered into the "Note Name" text
        entry box, only list note names that contain the entered
        text. (This is where incremental search happens.)
        """

        search_str = self.get_entered_note_name()
        note_names = self.notes.keys()

        # Remove strings that don't match
        if search_str:
            def string_matches_search(s):
                return search_str.lower() in s.lower()
            note_names = filter(string_matches_search, note_names)

        # Sort Alphabetically
        note_names = sorted(note_names, key=lambda s: s.lower())

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

    def open_note(self, note_name):
        """
        Open a note for editing.
        """

        note_filename = self.notes[note_name]
        note_path = os.path.join(self.notes_dir, note_filename)
        open_note(note_path, self.document_editor)

    ## GUI Callbacks
    def note_name_action_callback(self, *_args, **_kwargs):
        """
        A callback to perform an action based on the text in the "Note
        Name" text entry box.

        If the name of an existing note has been entered into the text
        box, open the note; if some other text has been entered,
        create a note with the entered text as a name; if no text has
        been entered, show a warning dialog box and do nothing.
        """

        note_name = self.get_entered_note_name()
        note_name = sanitize_note_name(note_name)
        if not note_name:
            messagebox.showwarning("Error", "Can't add note: no note name entered")
            return

        key = self.get_note_name_key(note_name)
        if key:
            # The note exists; open it.
            self.open_note(key)
        else:
            # The note doesn't exist; create it.
            # TODO popup a small confirmation/note setup dialog.
            note_filename = sanitize_note_name(note_name) + ".rtf"
            self.add_note(note_name, note_filename)
            self.clear_note_name_entry()
            self.open_note(note_name)
        self.clear_note_name_entry()

    def note_name_entry_changed(self, *_args, **_kwargs):
        """
        A callback to update the text entry action ("Open"/"Add")
        button's label, and update the incremental note list search,
        based on the text in the "Note Name" text entry box.
        """

        self.update_note_names_list()

        entered_note_name = self.get_entered_note_name()
        if self.get_note_name_key(entered_note_name):
            self.note_name_action_strvar.set("Open")
        else:
            self.note_name_action_strvar.set("Add")

    def clear_note_name_entry(self):
        """
        Clear the "Note Name" text entry box.
        """

        self.note_name_entry.delete(0, END)

    def open_note_from_listbox(self, *_args, **_kwargs):
        """
        If a note name has been selected in the note name list, open
        it; otherwise, show a warning dialog box and do nothing.
        """

        note_name = self.get_listbox_selected_note_name()
        if not note_name:
            # TODO show a warning dialog box or something
            messagebox.showwarning("Error", "Can't Open: No note selected")
            return
        self.open_note(note_name)

    def delete_note_from_listbox(self, *_args, **_kwargs):
        """
        If a note name has been selected in the note name list, delete
        it after prompting the user to confirm; otherwise, show a
        warning dialog box and do nothing.
        """

        note_name = self.get_listbox_selected_note_name()
        if not note_name:
            messagebox.showwarning("Error", "Can't Delete: No note selected")
            return
        if not messagebox.askyesno("Really Delete Note?",
                                   "WARNING: This will remove the note document file from your hard drive! You cannot undo this!\n\nReally remove '{0}'?".format(note_name),
                                   icon=messagebox.ERROR):
            return

        note_path = self.note_path(note_name)
        del(self.notes[note_name])
        self.save_notes_list()
        os.remove(note_path)
        self.update_note_names_list()

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
        note_name_entry = self.note_name_entry
        note_name_entry.pack(side=LEFT, fill=X, expand=True)
        note_name_entry.focus_set()
        note_name_entry.bind("<Return>", self.note_name_action_callback)
        note_name_entry.bind("<KP_Enter>", self.note_name_action_callback)

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
        note_names_listbox.bind("<Return>", self.open_note_from_listbox)
        note_names_listbox.bind("<KP_Enter>", self.open_note_from_listbox)
        note_names_listbox.bind("<Double-Button-1>", self.open_note_from_listbox)

        # Add scrollbar to list of notes
        notes_scrollbar = Scrollbar(notes_frame)
        notes_scrollbar.pack(side=LEFT, fill=Y)
        note_names_listbox.config(yscrollcommand=notes_scrollbar.set)
        notes_scrollbar.config(command=note_names_listbox.yview)

        ## Controls
        note_controls = Frame(notes_frame)
        note_controls.pack(side=LEFT, fill=Y)

        open_note_button = Button(note_controls, text="Open",
                                  command=self.open_note_from_listbox)
        open_note_button.pack(fill=X)

        delete_note_button = Button(note_controls, text="Delete",
                                    command=self.delete_note_from_listbox)
        delete_note_button.pack(fill=X)

        ## Final Initialization
        self.load_config()
        self.load_notes_list()
        self.update_note_names_list()

def maybe_first_time_setup():
    """
    Set up the user's notes directory/folder the first time they run
    NoteBag.
    """

    config = read_config(CONFIG_FILENAME)
    if config.get("NoteBag", "Notes Directory"):
       return True

    if not messagebox.askokcancel(
            "NoteBag Setup",
            "Hi! It looks like this is your first time running NoteBag!\n"
            "Please choose the folder where you would like NoteBag to keep your notes."
            ):
        return False

    notes_dir = filedialog.askdirectory(title="Notes Folder")
    print(notes_dir)
    if not notes_dir:
        return False

    config.set("NoteBag", "Notes Directory", notes_dir)
    save_config(config, CONFIG_FILENAME)
    return True


if __name__ == "__main__":
    # Hide the main root window, and only show the dialogs.
    root = Tk()
    root.withdraw()
    while not maybe_first_time_setup():
        if not messagebox.askretrycancel(
                "Try Again?",
                "It looks like your first-time setup failed. Would you like to try setting up NoteBag again?"
                ):
            root.destroy()
            exit(1)
    root.destroy()

    # Create the main window
    root = Tk()
    root.title("NoteBag")
    notebag = NoteBag(root)
    root.mainloop()
