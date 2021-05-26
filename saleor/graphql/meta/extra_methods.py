def extra_product_actions(instance, info, **data):
    info.context.plugins.product_updated(instance)


def extra_variant_actions(instance, info, **data):
    info.context.plugins.product_variant_updated(instance)


def extra_user_actions(instance, info, **data):
    info.context.plugins.customer_updated(instance)

def extra_checkout_actions(instance, info, **data):
    info.context.plugins.checkout_updated(instance)

MODEL_EXTRA_METHODS = {
    "Product": extra_product_actions,
    "ProductVariant": extra_variant_actions,
    "User": extra_user_actions,
    "Checkout": extra_checkout_actions,
}
