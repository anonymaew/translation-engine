import { exec } from './shell';
import { curryWrap, curryTop } from './curry';

const regex_footnotemark = /\[\^(\d+)\]/g;
const regex_footnote = /\[\^(\d+)\]:\s*(.*)/g;

const supportedExtensions = ['md', 'docx', 'txt', 'pdf'];

const convertToMD = ({ filename }: { filename: string }) => async () => {
  const fileExt = filename.split('.').pop();
  if (fileExt !== undefined && !supportedExtensions.includes(fileExt))
    return Promise.reject(`Unsupported file type: ${fileExt}`);

  await exec`rm -rf temp`.catch(
    e => (e.includes('No such file or directory'))
      ? Promise.reject(e) : Promise.resolve());

  console.log(`Converting ${filename} to markdown...`);

  const res = await exec`pandoc -t markdown --extract-media temp ${filename}`;
  return res;
}

const mdToFile = ({ filename }: { filename: string }) => async (md: string) => {
  const fileExt = filename.split('.').pop();
  const newFilename = `${filename.split('.').slice(0, -1)[0]}-translated.${fileExt}`

  const buf = new Response(md);
  console.log(`Converting back to ${newFilename} ...`);
  await exec`pandoc -o ${newFilename} -f markdown < ${buf}`;

  await exec`rm -rf temp`;
}

const fileToMDString = curryWrap(
  convertToMD,
  mdToFile
);

const stringToParagraphs = () => async (md: string) =>
  md
    .split('\n\n')
    .map(p => p
      .split('\n')
      .map(s => s.trim())
      .join(' ')
    );

const paragraphsToString = () => async (md: string[]) =>
  md.join('\n\n')

const splitByParagraphs = curryWrap(
  stringToParagraphs,
  paragraphsToString
);

const stringToSentences = () => async (md: string) => {
  const mod = md.replaceAll('。', '. ');
  const res = await exec`pandoc -t markdown < ${new Response(mod)}`;
  return res.split('\n')
    .map(p => p.trim())
    .map(p => (p === '') ? '\n' : p);
}

const sentencesToString = () => async (md: string[]) =>
  md.join('\n');

const splitBySentences = curryWrap(
  stringToSentences,
  sentencesToString
);

const removeFootnotes = curryTop(
  () => async (md: string) => {
    console.log('Removing footnotes...');
    return md
      .split('\n\n')
      .filter(p => !p.match(regex_footnote))
      .map(p => p.replace(regex_footnotemark, ''))
      .join('\n\n');
  }
);

const clumpParagraphs = (chars: number) => async (paragraphs: string[]) =>
  paragraphs
    .reduce((acc, p) => {
      if (acc.length === 0)
        return [p];
      if ((acc[acc.length - 1].length + p.length) < chars)
        return [...acc.slice(0, -1), acc[acc.length - 1] + '\n\n' + p];
      return [...acc, p];
    }, [] as string[])

const unclumpParagraphs = () => async (clumped: string[]) =>
  clumped
    .map(p => p.split('\n\n'))
    .flat();

const clumpText = curryWrap(
  clumpParagraphs,
  unclumpParagraphs
);

export {
  fileToMDString,
  splitByParagraphs,
  splitBySentences,
  removeFootnotes,
  clumpText
}
