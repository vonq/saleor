from api.tests import TestMigrations


class HasRemarksReasonTestCase(TestMigrations):

    migrate_from = "0083_alter_remarks_add_reason"
    migrate_to = "0084_populate_remarks_correctly"

    @property
    def app(self):
        return "products"

    def setUpBeforeMigration(self, apps):
        Product = apps.get_model("products", "Product")

        self.unmigrated_product = Product.objects.create(
            salesforce_id="73204450-3c56-5fee-a91d-0a43a222c3a6",
            remarks="",
            reason="",
        )

    def test_remarks_requirement_migrated(self):
        Product = self.apps.get_model("products", "Product")
        product = Product.objects.get(pk=self.unmigrated_product.id)
        self.assertEqual(
            product.remarks,
            "14-05-21 SF Blacklisted, because they can not facilitate our URL",
        )
