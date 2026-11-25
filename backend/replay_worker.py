from effects import calculate

def run(cx,kind,data):
    if kind!="sign_order_permutation":
        raise ValueError(kind)
    return calculate(cx,data["code"])
