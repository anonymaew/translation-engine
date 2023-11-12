# Translation Engine

The translation engine for the [Humanities in the Age of Artificial Intelligence](https://ai4humanities.sites.ucsc.edu/) research cluster.

## Developer Instructions

1. Generate an API key bay navigating to [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and logging in

2. This process is very straightforward. Copy your API key and store it somewhere safe and ideally encrypted (you will not be able to view it again)
    - I recommend storing it in a password manager like Bitwarden or 1Password

3. Open your terminal and enter the following command

    ```bash
    bash setup.sh
    ```

    - Note: if you are using Windows you will need to install Cygwin or use WSL in order to run bash scripts

4. If a config.env file is not found, the script will create it and you will be prompted to enter the API key that you just generated

5. Congratulations! You just generated your own API key and can now work on the project locally!

## Security

The following section is extremely important, **Read It Carefully**

- **Do not** commit API keys to the repository this poses a serious security risk
    - If you do this accidentilly, that's ok. Just let everyone know what happened, de-authorize your API key on the [website](https://platform.openai.com/api-keys), and generate a new one.
    - You MUST de-authorize your old key, because the nature of git means that the information is always recovorable, so deleting the file is not enough

- **Do not** share your API keys, if a key gets out then anyone who has it can use our API credits
    - If you need to be added to the OpenAI organization so that you can generate your own key, [contact Professor Minghui Hu](mailto:mhu@ucsc.edu) and ask him to add you

## Roadmap

- [ ] Explore open source LLM's
- [ ] Provide the model with relevant cultural and historical context for the translations
