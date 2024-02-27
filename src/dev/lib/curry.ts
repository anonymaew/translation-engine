interface CompositeFunc<C,I,O> {
  (config: C): (input: I) => Promise<O>;
}

// identity function
const identity = <C,I>(config: C) => async (input: I) => input;

// wraps two functions together (share same config) with a middle function
// suitable for pre/post processing
const curryWrap = <C,U,V>(
  fBefore: CompositeFunc<C,U,V>,
  fAfter: CompositeFunc<C,V,U>
) =>
  (config: C) => (fMid: (input: V) => Promise<V>) => async (prevRes: U) => {
    const resBefore = await fBefore(config)(prevRes);
    const resMid = await fMid(resBefore);
    const resAfter = await fAfter(config)(resMid);
    return resAfter;
  }

// top a mid function with preprocessing function
// use when there is no postprocessing function
const curryTop = <C,I>(f: CompositeFunc<C,I,I>) =>
  curryWrap(f, identity);

// compose multiple functions together
const curryCompose = <I,T extends I>(...fns: ((input: I) => T)[]) =>
  fns
    .reduceRight(
      (prev, curr) => curr(prev),
      (input: I) => input
    );

export { curryCompose, curryWrap, curryTop };
