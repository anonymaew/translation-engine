import ast
import json
import os
import re
<<<<<<< HEAD
import time
=======
from time import sleep, time
>>>>>>> 9a1e03d4de70f025d08808205d92f3737b48707a

import streamlit as st
from tqdm import tqdm

languages = ["Chinese", "English", "French", "Spanish"]
model_options = {
    "qwen2.5:7b": "Lightweight Model",
    "qwen2.5:32b": "Advanced Model",
    "Custom": None,
}
default_prompt = "You are an expert translator. Please translate the SOURCE language sentence into TARGET language accurately."


class TranslateForm:
    def __init__(self):
        self.input_list = [
            {
                "name": "src",
                "element": lambda key, val="Chinese": st.selectbox(
                    "Source Language", languages, index=languages.index(val), key=key
                ),
            },
            {
                "name": "tar",
                "element": lambda key, val="English": st.selectbox(
                    "Target Language", languages, index=languages.index(val), key=key
                ),
            },
            {
                "name": "model",
                "element": lambda key, val="": st.text_input(
                    "Model name", key=key, value=val
                ),
            },
            {
                "name": "temperature",
                "element": lambda key, val=0.2: st.slider(
                    "Temperature", 0.0, 1.0, val, 0.05, key=key
                ),
            },
            {
                "name": "context",
                "element": lambda key, val=9999: st.slider(
                    "Context Window Size", 512, 9999, val, 512, key=key
                ),
            },
            {
                "name": "prompt",
                "element": lambda key, val=default_prompt: st.text_area(
                    "Custom Prompt", value=val, key=key
                ),
            },
        ]

        if st.button("Load an existing configuration"):
            self.load("conf-translate")
        if st.button("Create a new configuration"):
            self.save("conf-translate")

        self.element = {}

        self.load_input()

        # Translate button

    def get(self):
        return self.element

    @st.dialog("Saving config")
    def save(self, mode):
        config_name = st.text_input("Config name")
        if st.button("Save") and config_name != "":
            if re.match("^[\\w-]+$", config_name) is not None:
                # Extract values from session state
<<<<<<< HEAD
                form_data = {
                    key: value
                    for key, value in st.session_state.items()
                    if key in self.element.keys()}
                #Make the json files and then put the data into the json file (json file can be found in data folder)
=======
                form_data = {key: st.session_state[key] for key in self.element.keys()}
>>>>>>> 9a1e03d4de70f025d08808205d92f3737b48707a
                os.makedirs(f"data/{mode}", exist_ok=True)
                with open(f"data/{mode}/{config_name}.json", "w") as f:
                    json.dump(form_data, f)

                #message display to say that it succesfully 
                st.success(f"Configuration '{config_name}' saved successfully!")
                # to have the message show up before 
                time.sleep(1.5)  
                st.rerun()
            else:
                st.error("The name must contains only alphanumeric or dashes only")

    @st.fragment
    def load_input(self, json_data=None):
        # for key, val in json_data.items():
        #     if key in self.element and key in st.session_state:
        #         print(st.session_state[key])
        #         st.session_state[key] = json_data[key]
        #         print(st.session_state[key])
        # st.rerun()
        for element in self.input_list:
            key = element["name"]
            # print(type(self.element[key]))
            if json_data is None:
                element["element"](key)
            else:
                element["element"](key, json_data[key])
            # print(st.session_state[key])

    @st.dialog("Loading an existing configuration")
    def load(self, mode):
        directory = f"data/{mode}"
        if not os.path.exists(directory):
            st.error(f"Configuration directory '{directory}' not found.")
            return
        files = map(
            lambda f: f[:-5],
            filter(
                lambda f: len(f) > 5 and f[-5:] == ".json", os.listdir(f"data/{mode}")
            ),
        )
        filename = st.selectbox("Saved configs", files)
        #to load the config file
        if st.button("Load"):
            file_path = f"{directory}/{filename}.json"
<<<<<<< HEAD
            try:
                with open(f"{directory}/{filename}.json","r") as f:
                    config_data = json.load(f)
                for key in self.element.keys():
                    if key in config_data:
                        st.session_state[key] = config_data[key]
                st.success(f"Loaded '{filename}'!")
                st.rerun()
            except Exception as e:
                st.error(f"Load failed: {str(e)}")
=======
            with open(file_path, "r") as f:
                config_data = json.load(f)
                self.load_input(config_data)
            # print(st.session_state)
>>>>>>> 9a1e03d4de70f025d08808205d92f3737b48707a
            # TODO: find the way to put dictionary's value into those input again


class ChatViewCLI:
    def __init__(self):
        self.bar = None
        self.now = 0

    def feedback(
        self, completed=None, all=None, user=None, assistant=None, status=None
    ):
        if completed is not None and all is not None:
            if completed == 0:
                self.bar = tqdm(range(all))
            completed += 1
            self.bar.update(completed - self.now)
            self.now = completed
        if user is not None:
            self.bar.write("[User]----------------------------------------")
            self.bar.write(user)
        if assistant is not None:
            self.bar.write("[Assistant]-----------------------------------")
            self.bar.write(assistant)


def sec_to_str(sec):
    min = sec / 60
    hour = min / 60
    return f"{f'{int(hour)}h ' if hour > 1 else ''}{f'{int(min % 60)}m ' if min > 1 else ''}{int(sec % 60)}s"


class ChatViewGUI:
    def __init__(self):
        self.spinner = st.status("Starting")
        self.progress_bar = st.progress(0, text="")
        self.chatbox = st.container(height=640, border=True)

        self.time_started = None
        self.time_finished = None

    def feedback(
        self, completed=None, all=None, user=None, assistant=None, status=None
    ):
        if completed is not None and all is not None:
            prog_str = f"Translated [{completed}/{all}]"
            if completed == 0:
                self.time_started = time()
                self.progress_bar.progress(0, text=prog_str)
            elif completed == all:
                if self.time_finished is None:
                    self.time_finished = time()
                self.progress_bar.progress(
                    1.0,
                    text=f"{prog_str} Time taken: {sec_to_str(self.time_finished - self.time_started)}",
                )
            else:
                et_sec = (time() - self.time_started) * (all - completed) / completed
                et_str = f"Estimated time left: {sec_to_str(et_sec)}"
                self.progress_bar.progress(
                    completed / all,
                    text=f"Translated [{completed}/{all}] {et_str}",
                )
        if user is not None:
            self.chatbox.chat_message("user").write(user)
        if assistant is not None:
            self.chatbox.chat_message("assistant").write(assistant)
        if status is not None:
            if status == "":
                self.spinner.update(label="Completed", state="complete")
            self.spinner.update(label=status)
