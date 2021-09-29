from api.tests import TestMigrations

from api.products.models import Product  # noqa


class ATSAvailabilityFlagMigrationTestCase(TestMigrations):
    migrate_from = "0091_alter_channel_type"
    migrate_to = "0092_auto_20210920_1054"

    @property
    def app(self):
        return "products"

    def setUpBeforeMigration(self, apps):
        Product = apps.get_model("products", "Product")  # type: Product

        Product.objects.create(
            status="Active",
            salesforce_id="product_1",
            title="Product 1",
            available_in_jmp=False,
            salesforce_product_type="Jobboard",
            duration_days=40,
        )

        Product.objects.create(
            status="Active",
            salesforce_id="product_2",
            title="Product 2",
            salesforce_product_type="Jobboard",
            duration_days=40,
        )

        Product.objects.create(
            status="Active",
            salesforce_id="product_2",
            title="Product 2",
            salesforce_product_type="Finance",
            duration_days=40,
        )

        Product.objects.create(
            status="Active",
            salesforce_id="product_1",
            title="Product 1",
            available_in_jmp=False,
            salesforce_product_type="Finance",
            duration_days=40,
        )

    def test_did_migrate_correctly(self):
        Product = self.apps.get_model("products", "Product")  # type: Product
        self.assertEqual(1, Product.objects.filter(available_in_ats=True).count())
