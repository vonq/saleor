from dataclasses import dataclass

from ajax_select import register, LookupChannel

from api.salesforce.sync import (
    get_accounts,
    get_accounts_by_ids,
    get_qprofile_accounts,
    get_accounts_by_qprofile_id,
)


@dataclass
class SFAccount:
    pk: str
    name: str

    def __str__(self):
        return self.pk


@register("account")
class AccountsLookup(LookupChannel):
    def get_query(self, q, request):
        accounts = get_accounts(query=q)

        return [SFAccount(name=obj["Name"], pk=obj["Id"]) for obj in accounts]

    def get_result(self, obj):
        return obj.pk

    def format_match(self, obj):
        return obj.name

    def get_objects(self, ids):
        accounts = get_accounts_by_ids(tuple(ids))
        return [SFAccount(pk=obj["Id"], name=obj["Name"]) for obj in accounts]

    def format_item_display(self, item):
        return u"<span class='account'>%s</span>" % item.name


@register("customer")
class CustomerLookup(AccountsLookup):
    def get_query(self, q, request):
        accounts = get_qprofile_accounts(query=q)
        return [
            SFAccount(name=obj["Name"], pk=obj["Qprofile_ID__c"]) for obj in accounts
        ]

    def get_objects(self, ids):
        accounts = get_accounts_by_qprofile_id(tuple(ids)[0])
        return [
            SFAccount(pk=obj["Qprofile_ID__c"], name=obj["Name"]) for obj in accounts
        ]
