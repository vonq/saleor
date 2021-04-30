def how_many_products_with_value(
    product_search_response, key: str, values: tuple, name_key="id"
):
    count = 0
    for product in product_search_response["results"]:
        for item in product[key]:
            if item[name_key] in values:
                count += 1
                break
    return count


def is_generic_product(product: dict) -> bool:
    """

    @rtype: object
    """
    return (
        0 == len(product["industries"])
        or any((industry["name"] == "Generic" for industry in product["industries"]))
        and 0 == len(product["job_functions"])
    )
