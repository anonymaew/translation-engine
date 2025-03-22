# import fitz
import re
import subprocess

import more_itertools
import pdf2docx

doc_dir = "./doc/"

regex_footnotemark = r"\[\^(\d+)\]"
regex_footnote = r"\[\^(\d+)\]:\s*(.*)"

supported_extensions = {"md": "markdown", "docx": "docx", "txt": "plain", "pdf": "pdf"}


def is_nothing(text):
    return text == "" or text == "\n" or text == "\n\n" or text == "."


class Document:
    def __init__(self, filename, file_content=None):
        self.filename = filename
        self.file_ext = filename.split(".")[-1]
        if self.file_ext not in supported_extensions.keys():
            raise ValueError(f"File extension not supported: {self.file_ext}")

        subprocess.run(["mkdir", "-p", doc_dir])
        subprocess.run(["rm", "-rf", doc_dir + "temp"])

        # if (file_content is None)
        #     subprocess.run(["cp", "-rf", doc_dir + "temp"])
        # else
        open(doc_dir + filename, "wb").write(file_content)

        print(f"Converting {filename} to markdown...")
        res = ""
        if self.file_ext == "pdf":
            doc = fitz.open(filename)
            for page in doc:
                res += page.get_text("text") + "\n\n"
        else:
            res = subprocess.run(
                [
                    "pandoc",
                    "-t",
                    "markdown",
                    "--wrap=none",
                    "--extract-media",
                    doc_dir + "temp",
                    doc_dir + filename,
                ],
                stdout=subprocess.PIPE,
            ).stdout.decode("utf-8")
        #     print('Conversion to PDF is partially supported, changing to docx...')
        #     self.filename = self.filename.replace('.pdf', '.docx')
        #     pdf2docx.parse(filename, self.filename)
        #     self.file_ext = 'docx'
        # res = subprocess.run(['pandoc', '-t', 'markdown', '--wrap=none',
        #                       '--extract-media', 'temp', self.filename],
        #                      stdout=subprocess.PIPE).stdout.decode('utf-8')
        self.md = res
        self.split_options = None

    def __str__(self):
        return self.md

    def split(self, split_options="sentences"):
        self.split_options = split_options
        if self.split_options == "sentences":
            return string_to_sentences(self.md)
        elif self.split_options == "paragraphs":
            return string_to_paragraphs(self.md)
        else:
            raise ValueError(f"Invalid split option: {self.split_options}")

    def export(self, jobs, file_ext=None):
        if self.split_options == "sentences":
            self.md = sentences_to_string(jobs)
        elif self.split_options == "paragraphs":
            self.md = paragraphs_to_string(jobs)
        else:
            raise ValueError(f"Invalid split option: {self.split_options}")

        if file_ext is None:
            file_ext = self.file_ext
        if file_ext not in supported_extensions.keys():
            raise ValueError(f"File extension not supported: {file_ext}")
        if file_ext == "pdf":
            print("Conversion to PDF is partially supported, changing to docx...")
            file_ext = "docx"

        new_filename = self.filename.replace(
            f".{self.file_ext}", f"-translated.{file_ext}"
        )

        print(f"Converting back to {new_filename}...")
        subprocess.run(
            [
                "pandoc",
                "-o",
                doc_dir + new_filename,
                "-t",
                supported_extensions[file_ext],
                "-f",
                "markdown",
            ],
            input=self.md.encode("utf-8"),
        )

        subprocess.run(["rm", "-rf", doc_dir + "temp"])
        return (doc_dir, new_filename)


def string_to_paragraphs(md):
    paragraphs = md.split("\n\n")
    paragraphs_clean = list(map(lambda p: " ".join(p.split("\n")), paragraphs))
    return paragraphs_clean


def paragraphs_to_string(paragraphs):
    return "\n\n".join(paragraphs)


def string_to_sentences(md):
    fix_dots = md.replace("。", ". ")
    paragraphs = fix_dots.split("\n\n")
    sentences = list(map(lambda p: p.split(". "), paragraphs))
    sentences_clean = list(
        map(lambda p: list(filter(lambda s: not is_nothing(s), p)), sentences)
    )
    sentences_dot = list(
        map(lambda p: list(map(lambda s: s + ".", p)) + [""], sentences_clean)
    )
    sentences_str = list(more_itertools.collapse(sentences_dot))
    return sentences_str


def sentences_to_string(sentences):
    return "\n".join(sentences)


def remove_footnotes_func(_):
    def f(md):
        paragraphs = md.split("\n\n")
        paragraphs_no_footnotes = filter(
            lambda p: not re.compile(regex_footnote).match(p), paragraphs
        )
        paragraphs_no_footnotes = list(
            map(lambda p: re.sub(regex_footnotemark, "", p), paragraphs_no_footnotes)
        )
        str_no_footnotes = "\n\n".join(paragraphs_no_footnotes)
        return str_no_footnotes

    return f
