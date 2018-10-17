def sum_production_dicts(prod1: dict, prod2: dict()):
    """
    Sum two productions dictionnaries. For a production mode key, if both
    values are None, the result is None. Else, the None is replaced by zero
    """
    to_return = prod1.copy()
    for prod_name, value2 in prod2.items():
        value1 = to_return.get(prod_name)
        if value1 is None and value2 is None:
            continue
        to_return[prod_name] = (value1 or 0) + (value2 or 0)
    return to_return


def nan_to_zero(v):
    if math.isnan(v):
        return 0
    return v
