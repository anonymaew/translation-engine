import os
import subprocess
from time import sleep

import streamlit as st

from lib.chatagent import OllamaAgent, OpenAIAgent
from lib.doctext import Document
from lib.gui import ChatViewGUI, TranslateForm
from lib.kube import deploy_from_yml, port_forward
from lib.translate import EntityAgent

file = None


def main():
    st.title("Configuration for translation engine")

    uploaded_file = st.file_uploader(
        "Upload Document", type=["docx", "txt", "pdf", "md"]
    )
    form = TranslateForm()

    # Translate button
    if st.button("Translate"):
        form_result = form.get()
        # translate_main_options = {
        #     "model": selected_model if selected_model != "Custom" else model_name,
        #     "options": {
        #         "temperature": temperature,
        #         "num_ctx": num_ctx,
        #     },
        #     "prompt": prompt,
        # }
        form_result["options"] = {
            "temperature": form_result["temperature"],
            "num_ctx": form_result["context"],
        }
        print(uploaded_file.name)
        print(form_result)

        gui = ChatViewGUI()
        gui.feedback(status="Preparing resources on Kubernetes cluster")
        deploy_from_yml("deploy.yml")
        port_forward("ollama", 11434)
        agent = OllamaAgent("localhost:11434")
        gui.feedback(status="Ingesting file")
        file = Document(uploaded_file.name, uploaded_file.read())
        jobs = file.split("paragraphs")
        gui.feedback(status="Translating")
        translated = agent.task(jobs, form_result, feedback=gui.feedback)
        gui.feedback(status="Exporting result back to file")
        new_filename = file.export(translated)
        gui.feedback(status="")

        st.download_button(
            "Translated file",
            data=open("/".join(new_filename), "rb").read(),
            file_name=new_filename[1],
        )


if __name__ == "__main__":
    main()
