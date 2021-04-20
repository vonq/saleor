from api.tests import TestMigrations


class HasHtmlTestCase(TestMigrations):

    migrate_from = "0063_hotfix_clear_logo_on_18552"
    migrate_to = "0064_auto_20210408_1114"

    @property
    def app(self):
        return "products"

    def setUpBeforeMigration(self, apps):
        Product = apps.get_model("products", "Product")

        self.unmigrated_product = Product.objects.create(
            status="Negotiated",
            title="Construction board",
            salesforce_product_type="job board",
        )

        Product.objects.create(
            status="Negotiated",
            title="Low duration board",
            duration_days=10,
            salesforce_product_type="job board",
        )

        self.migrated_product = Product.objects.create(
            status="Negotiated",
            has_html_posting=True,
            title="Engineering Board",
            salesforce_product_type="job board",
        )

        Product.objects.create(
            status="Negotiated",
            title="General",
            salesforce_product_type="job board",
            duration_days=20,
        )

    def test_html_requirement_migrated(self):
        Product = self.apps.get_model("products", "Product")
        product = Product.objects.get(pk=self.migrated_product.id)
        self.assertEqual(
            product.posting_requirements.filter(
                posting_requirement_type="HTML Posting"
            ).count(),
            1,
        )
        product = Product.objects.get(pk=self.unmigrated_product.id)
        self.assertEqual(product.posting_requirements.count(), 0)
