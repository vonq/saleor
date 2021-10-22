from graphene_federation import build_schema

from saleor.graphql.account.schema import AccountMutations, AccountQueries
from saleor.graphql.app.schema import AppMutations, AppQueries
from saleor.graphql.attribute.schema import AttributeMutations, AttributeQueries
from saleor.graphql.channel.schema import ChannelMutations, ChannelQueries
from saleor.graphql.checkout.schema import CheckoutMutations
from saleor.graphql.core.enums import unit_enums
from saleor.graphql.core.schema import CoreMutations, CoreQueries
from saleor.graphql.csv.schema import CsvMutations, CsvQueries
from saleor.graphql.discount.schema import DiscountMutations, DiscountQueries
from saleor.graphql.giftcard.schema import GiftCardMutations, GiftCardQueries
from saleor.graphql.invoice.schema import InvoiceMutations
from saleor.graphql.menu.schema import MenuMutations, MenuQueries
from saleor.graphql.meta.schema import MetaMutations
from saleor.graphql.order.schema import OrderMutations, OrderQueries
from saleor.graphql.page.schema import PageMutations, PageQueries
from saleor.graphql.payment.schema import PaymentMutations, PaymentQueries
from saleor.graphql.plugins.schema import PluginsMutations, PluginsQueries
from saleor.graphql.product.schema import ProductMutations, ProductQueries
from saleor.graphql.shipping.schema import ShippingMutations, ShippingQueries
from saleor.graphql.shop.schema import ShopMutations, ShopQueries
from saleor.graphql.translations.schema import TranslationQueries
from saleor.graphql.warehouse.schema import StockQueries, WarehouseMutations, WarehouseQueries
from saleor.graphql.webhook.schema import WebhookMutations, WebhookQueries
from vonq.mutations import ExternalObtainAccessTokens
from vonq.queries import CheckoutQueries


class Query(
    AccountQueries,
    AppQueries,
    AttributeQueries,
    ChannelQueries,
    CoreQueries,
    CsvQueries,
    DiscountQueries,
    PluginsQueries,
    GiftCardQueries,
    MenuQueries,
    OrderQueries,
    PageQueries,
    PaymentQueries,
    ProductQueries,
    ShippingQueries,
    ShopQueries,
    StockQueries,
    TranslationQueries,
    WarehouseQueries,
    WebhookQueries,
    CheckoutQueries,
):
    pass


# Monkey patch this to be able to expose a different set of tokens to the frontend
AccountMutations.external_obtain_access_tokens = ExternalObtainAccessTokens.Field()


class Mutation(
    AccountMutations,
    AppMutations,
    AttributeMutations,
    ChannelMutations,
    CheckoutMutations,
    CoreMutations,
    CsvMutations,
    DiscountMutations,
    PluginsMutations,
    GiftCardMutations,
    InvoiceMutations,
    MenuMutations,
    MetaMutations,
    OrderMutations,
    PageMutations,
    PaymentMutations,
    ProductMutations,
    ShippingMutations,
    ShopMutations,
    WarehouseMutations,
    WebhookMutations,
):
    pass


schema = build_schema(Query, mutation=Mutation, types=unit_enums)
