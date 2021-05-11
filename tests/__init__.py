import time
from abc import ABCMeta, abstractmethod
from typing import List, Tuple

from algoliasearch_django import AlgoliaIndex, algolia_engine
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.models import Model
from django.test import TestCase, override_settings

from django.conf import settings

User = get_user_model()


class AuthenticatedTestCase(TestCase):
    def setUp(self) -> None:
        user = User.objects.create(username="test", password="test")
        self.client.force_login(user)


class TestMigrations(TestCase):
    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name

    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert (
            self.migrate_from and self.migrate_to
        ), "TestCase '{}' must define migrate_from and migrate_to     properties".format(
            type(self).__name__
        )
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    @abstractmethod
    def setUpBeforeMigration(self, apps):
        raise NotImplementedError


NOW = int(time.time())


@override_settings(
    ALGOLIA={
        "INDEX_SUFFIX": f"{__name__}_{NOW}",
        "APPLICATION_ID": settings.ALGOLIA["APPLICATION_ID"],
        "API_KEY": settings.ALGOLIA["API_KEY"],
        "AUTO_INDEXING": True,
    }
)
class SearchTestCase(AuthenticatedTestCase, metaclass=ABCMeta):
    @property
    @abstractmethod
    def model_index_class_pairs(self) -> List[Tuple[Model, AlgoliaIndex]]:
        pass

    @classmethod
    @abstractmethod
    def setUpSearchClass(cls):
        pass

    """
    We need to gather all the product-search related tests into
    this one class, as we're hitting the live algolia index.
    This means that we need to create the index and populate
    it with test entities. This might take quite some time,
    and it's infeasible to do it on a setUp method.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        algolia_engine.reset(settings.ALGOLIA)
        for model_index_pair in cls.model_index_class_pairs:
            model_class, index_class = model_index_pair
            if not algolia_engine.is_registered(model_class):
                algolia_engine.register(model_class, index_class)
                algolia_engine.reindex_all(model_class)

        cls.setUpSearchClass()

        for model_index_pair in cls.model_index_class_pairs:
            model_class, _ = model_index_pair
        algolia_engine.reindex_all(model_class)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for model_index_pair in cls.model_index_class_pairs:
            _, index_class = model_index_pair
            algolia_engine.client.init_index(
                f"{index_class.index_name}_{__name__}_{NOW}"
            ).delete()
        algolia_engine.reset(settings.ALGOLIA)
