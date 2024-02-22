const curryWrap = (
  fBefore: () => Promise<any>,
  fAfter: () => Promise<any>
) =>
  (...config) => (fMid: () => Promise<any>) => async (prevRes) => {
    const resBefore = await fBefore(...config)(prevRes);
    const resMid = await fMid(resBefore);
    const resAfter = await fAfter(...config)(resMid);
    return resAfter;
  }

const curryCompose = (...fns) =>
  fns
    .reduceRight((acc, fn) => fn(acc),
      (x) => x);

export { curryCompose, curryWrap };
