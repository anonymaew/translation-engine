import functools


# identity function
def identity(_): return lambda x: x


# wraps two functions together (share same config) with a middle function
# suitable for pre/post processing
def curry_wrap(f_before, f_after):
    return lambda *args: lambda f_mid: lambda prev_res: \
        f_after(args)(
            f_mid(
                f_before(args)(prev_res)
            )
        )


# top a mid function with preprocessing function
# use when there is no postprocessing function
def curry_top(f): return curry_wrap(f, identity)


# compose multiple functions
def curry_compose(fs): return functools.reduce(
    lambda f, g: g(f), reversed(fs), lambda x: x)
