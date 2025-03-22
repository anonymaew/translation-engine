import ast
import json
import os
import re
from time import time

import streamlit as st

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
                "element": lambda key: st.selectbox(
                    "Source Language", languages, index=0, key=key
                ),
            },
            {
                "name": "tar",
                "element": lambda key: st.selectbox(
                    "Target Language", languages, index=1, key=key
                ),
            },
            {
                "name": "model",
                "element": lambda key: st.text_input("Model name", key=key),
            },
            {
                "name": "temperature",
                "element": lambda key: st.slider(
                    "Temperature", 0.0, 1.0, 0.2, 0.05, key=key
                ),
            },
            {
                "name": "context",
                "element": lambda key: st.slider(
                    "Context Window Size", 512, 9999, 9999, 512, key=key
                ),
            },
            {
                "name": "prompt",
                "element": lambda key: st.text_area(
                    "Custom Prompt", value=default_prompt, key=key
                ),
            },
        ]

        if st.button("Load an existing configuration"):
            self.load("conf-translate")
        if st.button("Create a new configuration"):
            self.save("conf-translate")

        self.element = {}

        for element in self.input_list:
            self.element[element["name"]] = element["element"](element["name"])

        # Translate button

    def get(self):
        return self.element

    @st.dialog("Saving config")
    def save(self, mode):
        config_name = st.text_input("Config name")
        if st.button("Save") and config_name != "":
            if re.match("^[\\w-]+$", config_name) is not None:
                # TODO: find the way to extract those input values above
                # into dictonary, then convert it to JSON.
                # may start from this: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
                open(f"data/{mode}/{config_name}.json", "w").write(the_data)
                st.rerun()
            else:
                st.error("The name must contains only alphanumeric or dashes only")

    @st.dialog("Loading an existing configuration")
    def load(self, mode):
        files = map(
            lambda f: f[:-5],
            filter(
                lambda f: len(f) > 5 and f[-5:] == ".json", os.listdir(f"data/{mode}")
            ),
        )
        filename = st.selectbox("Saved configs", files)
        if st.button("Load"):
            json_str = open(f"data/{mode}/{filename}.json", "r").read()
            # TODO: find the way to put dictionary's value into those input again


def feedback(_completed=None, _all=None, _user=None, _assistant=None):
    pass


def sec_to_str(sec):
    min = sec / 60
    hour = min / 60
    return f"{f'{int(hour)}h ' if hour > 1 else ''}{f'{int(min % 60)}m ' if min > 1 else ''}{int(sec % 60)}s"


class ChatView:
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
