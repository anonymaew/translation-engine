# from lib.translate import replace_translate_nouns
from lib.chatagent import OllamaAgent, OpenAIAgent
from lib.doctext import Document
from lib.gui import ChatViewCLI
from lib.kube import deploy_from_yml, port_forward
from lib.translate import EntityAgent

filename = "chinese-text.docx"
src = "Chinese"
tar = "English"

translate_entity_options = {
    # 'model': 'jack/llama3-8b-chinese:latest',
    "model": "qwen2.5:7b",
    "options": {
        "temperature": 0.8,
        "num_ctx": 9999,
    },
    # 'prompt': f'Romanize the following list of {src} entities into {tar}, present in dash bullet points and do not include the original {src} language.',
    "prompt": f"Ignore the {tar} text. Please translate the given {src} entity into {tar}, only give one concise translation result.",
    # 'user_prompt': lambda text, paragraph: f"Translate the entity from {src} to {tar}\n\n{src} entity: {text}\n\n{tar}: ",
}
extract_entity_options = {
    "src": src,
    "label": [
        "PERSON",
        "GPE",
        "LOC",
        "ORG",
        "FAC",
        "EVENT",
        "NORP",
        "WORK_OF_ART",
        "PRODUCT",
    ],
    # 'label': ['PERSON', 'LOC', 'WORK_OF_ART'],
}
translate_main_options = {
    # 'model': 'jack/llama3-8b-chinese:latest',
    "model": "qwen2.5:72b",
    "options": {
        # 'temperature': 0,
        # 'num_ctx': 9999,
    },
    "prompt": f"You are an expert translator. Please translate the {src} language sentence into {tar} language using the vocabulary and expressions of the native speaker of the {tar} language. Please translate the footnotes and retain their original format and quotes. Please use a concise, clear, and formal tone of voice and academic writing style. Please do not give any alternative translation or including any notes or discussion.",
    "user_prompt": lambda src_sentence: f"""
    You will be provided source sentences in {src} to translate in into {tar} similar to the ones below:

    {src}: 行己有耻，博学于文。封建之失，其专在下；郡县之失，其专在上。
    {tar}: A sense of shame should guide one's moral practice, and scholarly erudition is revealed in cultural scope. The shortcomings of the systemof enfeoffment are concentrated at the bottom of the society, whereas the weakness of the system of central administration are concentrated at the top of society.
    {src}: 新制度论恢复了道德评价与制度的内在关联，但这一恢复不是单纯地将制度及其关系视为道德评价的根据，而是将制度纳入道德范畴内部，即在儒学的框架内重新恢复礼乐与制度的一致性。
    {tar}: The new thoery of institutions restored the intrinsic relationship between moral evaluation and institutions, but this restoration did not simply regard institutions and the relationships they regulated as the basis of moral evaluation.
    {src}: 在这一背景下，黄宗羲、顾炎武等以遗民身份进行了艰苦卓绝的抗战，在他们的思想和学术中贯注着以"夷夏之辨"表述的族群/正统思想。但是，族群意识或夷夏之辨不足以概括顾炎武、黄宗羲的批判性思想的特征。
    {tar}: Against this backdrop, Huang Zongxi and Gu Yanwu carried out an arduous struggle as Ming loyalists against the conquest dynasty. Their thought and scholarship were preoccupied with the distinction between the Chinese and barbarians, orthodoxy and heterodoxy, expressed in Confucian language as "discerning the Chinese from the barbarians"(Yixia zhibian). However, the ethnic consciousness of "discerning the Chinese from the barbarians" cannnot fully characterize Gu Yanwu and Huang Zongxi's
    thinking.
    {src}: 正是在这一语境中，人们对顾炎武思想的研究集中于"民族"或"种族"意识之上，反而多少忽略了他的思想的更为复杂的方面。
    {tar}: In this intellectual circumstance, hisotrical research on Gu Yanwu's thought has focused on his "national" or "ethnic" consciousness but has somewhat ignored the more complicated aspects of his intellectual formation.

    You are an expert translator. I am going to give you one or more example pairs of text snippets where the first is in {src} and the second is a translation of the first snippet into {tar}. The sentence will be writtern

    {src}: <first sentence>
    {tar}: <translated first sentence>
    After the example pairs, I am going to provide another sentence in {src} and I want you to translate it into {tar}. Give only the translation, and no extran commentary, formatting, or chattiness. Translate the text from {src} to {tar}.

    {src}: {src_sentence}
    {tar}:
    """,
}


if __name__ == "__main__":
    deploy_from_yml("deploy.yml")
    port_forward("ollama", 11434)
    agent = OllamaAgent("localhost:11434")
    # agent = OpenAIAgent()
    # entity = EntityAgent(agent, extract_entity_options)
    file = Document(filename, open(filename, "rb").read())
    # file.md = entity.task(str(file), translate_entity_options)
    jobs = file.split("paragraphs")
    cli = ChatViewCLI()
    translated = agent.task(jobs, translate_main_options, feedback=cli.feedback)
    file.export(translated)
