const identity = () => async (x) => x;

const logs = [];

const curryWrap = (
  fBefore: () => Promise<any>,
  fAfter: () => Promise<any>
) =>
  (...config) => (fMid: () => Promise<any>) => async (prevRes) => {
    const fBeforeStart = Date.now();
    const resBefore = await fBefore(...config)(prevRes);
    const fBeforeTime = ((Date.now() - fBeforeStart)/1000).toFixed(3);
    logs.push(`${fBefore.name}: ${fBeforeTime} seconds`);

    const resMid = await fMid(resBefore);

    const fAfterStart = Date.now();
    const resAfter = await fAfter(...config)(resMid);
    const fAfterTime = ((Date.now() - fAfterStart)/1000).toFixed(3);
    logs.push(`${fAfter.name}: ${fAfterTime} seconds`);
    return resAfter;
  }

const curryTop = (f: () => Promise<any>) =>
  curryWrap(f, identity);

const curryCompose = (...fns) => {
  const res = fns
    .reduceRight((acc, fn) => fn(acc),
      (x) => x);
  logs.forEach(log => console.log(log));
  return res;
};

export { curryCompose, curryWrap, curryTop };
