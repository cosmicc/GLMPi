
def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

def float_trunc_1dec(num):
    try:
        tnum = num // 0.1 / 10
    except:
        return False
    else:
        return tnum

def c2f(c):
    return float_trunc_1dec((c*9/5)+32)


