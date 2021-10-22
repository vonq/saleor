from api.tests import TestMigrations


class TruncateChannelNameAndAlterTable(TestMigrations):
    migrate_from = "0086_populate_remarks_for_active_products"
    migrate_to = "0088_auto_20210629_1027"

    @property
    def app(self):
        return "products"

    def setUpBeforeMigration(self, apps):
        Channel = apps.get_model("products", "Channel")
        self.unmigrated_channel = Channel.objects.create(
            name="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas hendrerit, erat a rhoncus posuere.",
        )

    def test_migrate_correctly(self):
        Channel = self.apps.get_model("products", "Channel")
        channel = Channel.objects.get(pk=self.unmigrated_channel.id)
        self.assertEqual(
            channel.name,
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas hendrerit, e…",
        )
