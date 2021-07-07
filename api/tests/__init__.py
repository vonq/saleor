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
