from algoliasearch_django.decorators import disable_auto_indexing
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, tag
from django.urls import reverse

from api.products.models import Product, Industry, JobFunction
from api.vonqtaxonomy.models import (
    JobCategory as VonqJobCategory,
    Industry as VonqIndustry,
)

User = get_user_model()


@tag("unit")
@disable_auto_indexing
class AdminPermissionsTestCase(TestCase):
    def setUp(self) -> None:

        base_perms = Permission.objects.filter(
            name__in=[
                "Can change product",
                "Can view product",
            ]
        )

        self.procurement_group = Group.objects.create(name="Procurement")
        self.procurement_group.permissions.set(base_perms)
        self.procurement_group.save()

        self.user = User.objects.create(
            username="procurement", password="password", is_staff=True
        )
        self.user.groups.add(self.procurement_group)
        self.user.save()

        self.product = Product.objects.create(
            title="Example product",
        )

        vonq_industry = VonqIndustry.objects.create(mapi_id=1, name="Something")
        vonq_function = VonqJobCategory.objects.create(mapi_id=1, name="Something")

        ind = Industry.objects.create(
            name="Something", vonq_taxonomy_value_id=vonq_industry.id
        )
        jf = JobFunction.objects.create(
            name="Something else", vonq_taxonomy_value_id=vonq_function.id
        )
        self.product.industries.add(ind)
        self.product.job_functions.add(jf)
        self.product.save()

    def test_user_cannot_see_industries_and_functions(self):
        self.client.force_login(self.user)

        resp = self.client.get(f"/admin/products/product/{self.product.id}/change/")

        self.assertEqual(200, resp.status_code)
        self.assertNotIn(b'class="form-row field-industries"', resp.content)
        self.assertNotIn(b'class="form-row field-job_functions"', resp.content)

    def test_can_see_industries_and_functions_but_not_edit(self):
        self.client.force_login(self.user)
        view_perms = Permission.objects.filter(
            name__in=[
                "Can view product job functions",
                "Can view product industries",
            ]
        )
        self.procurement_group.permissions.add(*view_perms)
        self.procurement_group.save()

        resp = self.client.get(f"/admin/products/product/{self.product.id}/change/")
        self.assertEqual(200, resp.status_code)
        self.assertIn(b'class="form-row field-industries"', resp.content)
        self.assertIn(b'class="form-row field-job_functions"', resp.content)
        self.assertNotIn(
            b'<p id="id_job_functions_filter" class="selector-filter">', resp.content
        )
        self.assertNotIn(
            b'<p id="id_industries_filter" class="selector-filter">', resp.content
        )

    def test_can_edit_industries_and_functions(self):
        self.client.force_login(self.user)
        view_perms = Permission.objects.filter(
            name__in=[
                "Can change product job functions",
                "Can change product industries",
            ]
        )
        self.procurement_group.permissions.add(*view_perms)
        self.procurement_group.save()

        resp = self.client.get(f"/admin/products/product/{self.product.id}/change/")

        self.assertEqual(200, resp.status_code)
        self.assertIn(b'class="form-row field-industries"', resp.content)
        self.assertIn(b'class="form-row field-job_functions"', resp.content)
        self.assertIn(
            b'<select name="job_functions" id="id_job_functions" multiple class="selectfilter"',
            resp.content,
        )
        self.assertIn(
            b'<select name="industries" id="id_industries" multiple class="selectfilter',
            resp.content,
        )


@tag("unit")
class TestAdminRedirect(TestCase):
    @disable_auto_indexing()
    def setUp(self) -> None:
        self.product = Product.objects.create(
            title="Example", salesforce_id="3f8cb2df-9e08-5982-b97e-edd8b96c6cd9"
        )

    def test_redirect_from_sf_to_django_admin(self):
        resp = self.client.get(
            reverse("saleforce-edit", args=(self.product.salesforce_id,))
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.headers["Location"],
            f"/admin/products/product/{self.product.id}/change/",
        )
