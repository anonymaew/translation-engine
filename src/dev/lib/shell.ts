import { $ } from 'bun';

const checkProgram = async (program: string) => {
  const has = Bun.which(program) !== null;
  if (!has)
    return Promise.reject(`Program "${program}" not found`);
  return Promise.resolve();
};

const exec = async (strings: TemplateStringsArray, ...values: any[]) => {
  const { stdout, stderr, exitCode } = await $(strings, ...values).quiet();
  if (exitCode !== 0)
    return Promise.reject(stderr.toString());
  return stdout.toString();
}

export { checkProgram, exec };
