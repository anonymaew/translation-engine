from .curry import curry_wrap, curry_top
import more_itertools
import subprocess
import re

regex_footnotemark = r'\[\^(\d+)\]'
regex_footnote = r'\[\^(\d+)\]:\s*(.*)'

supported_extensions = ['md', 'docx', 'txt', 'pdf']


def is_nothing(text):
    return text == '' or text == '\n' or text == '\n\n' or text == '.'


def convert_to_md(config):
    def f(_):
        filename = config[0]
        file_ext = filename.split('.')[-1]
        if file_ext not in supported_extensions:
            raise ValueError(f'File extension not supported: {file_ext}')

        subprocess.run(['rm', '-rf', 'temp'])

        print(f'Converting {filename} to markdown...')
        res = subprocess.run(['pandoc', '-t', 'markdown', '--wrap=none',
                             '--extract-media', 'temp', filename], stdout=subprocess.PIPE).stdout.decode('utf-8')
        return res
    return f


def md_to_file(config):
    def f(md):
        filename = config[0]
        file_ext = filename.split('.')[-1]
        new_filename = filename.replace(
            f'.{file_ext}', f'-translated.{file_ext}')
        print(f'Converting back to {new_filename}...')
        subprocess.run(['pandoc', '-o', new_filename, '-t',
                       file_ext, '-f', 'markdown'], input=md.encode('utf-8'))

        subprocess.run(['rm', '-rf', 'temp'])
    return f


file_to_md_string = curry_wrap(convert_to_md, md_to_file)


def string_to_paragraphs(_):
    def f(md):
        paragraphs = md.split('\n\n')
        paragraphs_clean = list(
            map(lambda p: ' '.join(p.split('\n')), paragraphs))
        return paragraphs_clean
    return f


def paragraphs_to_string(_):
    def f(paragraphs):
        return '\n\n'.join(paragraphs)
    return f


split_by_paragraphs = curry_wrap(string_to_paragraphs, paragraphs_to_string)


def string_to_sentences(_):
    def f(md):
        fix_dots = md.replace('。', '. ')
        paragraphs = fix_dots.split('\n\n')
        sentences = list(map(lambda p: p.split('. '), paragraphs))
        sentences_clean = list(
            map(lambda p: list(filter(lambda s: not is_nothing(s), p)), sentences))
        sentences_dot = list(
            map(lambda p: list(map(lambda s: s + '.', p)) + [''], sentences_clean))
        sentences_str = list(more_itertools.collapse(sentences_dot))
        return sentences_str
    return f


def sentences_to_string(_): return lambda sentences: \
    '\n'.join(sentences)


split_by_sentences = curry_wrap(string_to_sentences, sentences_to_string)


def remove_footnotes_func(_):
    def f(md):
        paragraphs = md.split('\n\n')
        paragraphs_no_footnotes = filter(
            lambda p: not re.compile(regex_footnote).match(p), paragraphs)
        paragraphs_no_footnotes = list(map(
            lambda p: re.sub(regex_footnotemark, '', p), paragraphs_no_footnotes))
        str_no_footnotes = '\n\n'.join(paragraphs_no_footnotes)
        return str_no_footnotes
    return f


remove_footnotes = curry_top(remove_footnotes_func)
