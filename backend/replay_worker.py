from effects import calculate


def run(cx, kind, data):
    if kind != "sign_order_permutation":
        raise ValueError(kind)
    # 任务载荷携带发起时的修订轮次；旧轮次任务由 calculate 拒绝
    return calculate(cx, data["code"], data.get("revision"))
