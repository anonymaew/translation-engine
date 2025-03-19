import os
import subprocess
from time import sleep

import streamlit as st

# from lib.chatagent import OllamaAgent, OpenAIAgent
# from lib.doctext import Document
# from lib.translate import EntityAgent
# from lib.kube import deploy_from_yml
# from lib.translate import replace_translate_nouns
from lib.chatagent import OllamaAgent, OpenAIAgent
from lib.doctext import Document
from lib.kube import deploy_from_yml
from lib.translate import EntityAgent

file = None


# def notify():


def main():
    st.title("Translation engine")

    # Upload file
    uploaded_file = st.file_uploader(
        "Upload Document", type=["docx", "txt", "pdf", "md"]
    )
    # st.write(uploaded_file)
    # temporary impolementation, will change to  the above logic later
    # filename = st.text_area("Filename")

    # Select source and target language
    src = st.selectbox(
        "Source Language", ["Chinese", "English", "French", "Spanish"], index=0
    )
    tar = st.selectbox(
        "Target Language", ["Chinese", "English", "French", "Spanish"], index=1
    )

    # Select translation model
    model_options = {
        "qwen2.5:7b": "Lightweight Model",
        "qwen2.5:32b": "Advanced Model",
        "Custom": None,
    }
    selected_model = st.selectbox(
        "Select Translation Model",
        list(model_options.keys()),
        format_func=lambda x: f"{x} - {model_options[x]}"
        if model_options[x] is not None
        else x,
    )
    if selected_model == "Custom":
        model_name = st.text_input("Custom model from ollama.com/library")

    # Set model parameters
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    num_ctx = st.slider("Context Window Size", 512, 9999, 9999, 512)

    # Custom prompt
    default_prompt = f"You are an expert translator. Please translate the {src} language sentence into {tar} language accurately."
    prompt = st.text_area("Custom Prompt", value=default_prompt)

    # Translate button
    if st.button("Translate"):
        translate_main_options = {
            "model": selected_model if selected_model != "Custom" else model_name,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
            },
            "prompt": prompt,
            #'user_prompt': lambda src_sentence: f"""{multishots_instruction}
            # You are an expert translator. I am going to give you one or more example pairs of text snippets where the first is in {src} and the second is a translation of the first snippet into {tar}. The sentence will be writtern
            # {src}: <first sentence>
            # {tar}: <translated first sentence>
            # After the example pairs, I am going to provide another sentence in {src} and I want you to translate it into {tar}. Give only the translation, and no extran commentary, formatting, or chattiness. Translate the text from {src} to {tar}.
            # {src}: {src_sentence}
            # {tar}:
            # """
        }

        # prepare files
        filename = ".tmp/" + uploaded_file.name
        if uploaded_file is None:
            return
        # subprocess.run(["rm", "-f", filename])
        open(filename, "wb").write(uploaded_file.read())

        deploy_from_yml("deploy.yml")
        agent = OllamaAgent()
        # agent = OpenAIAgent()
        # entity = EntityAgent(agent, extract_entity_options)
        file = Document(filename)
        # file.md = entity.task(str(file), translate_entity_options)
        jobs = file.split("paragraphs")
        translated = agent.task(jobs, translate_main_options)
        # rewrited = agent.task(jobs, rewriting_options)
        new_filename = file.export(translated)
        # file.export(rewrited)
        # new_content =

        st.download_button(
            "Translated file",
            data=open(new_filename, "rb").read(),
            file_name=new_filename[5:],
        )
    # code = st.code("")
    # for i in range(10):
    #     code.
    #     sleep(1)


# filename = '《人种》.docx'


if __name__ == "__main__":
    main()
