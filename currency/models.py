from django.utils import timezone

from django.db import models


class Currency(models.Model):
    code = models.CharField(max_length=3, null=False, blank=False)
    name = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code} // {self.name}"


class ExchangeRate(models.Model):
    target_currency = models.ForeignKey("Currency", on_delete=models.CASCADE)
    rate = models.DecimalField(
        decimal_places=5, max_digits=20
    )  # conversion rate against EUR
    date = models.DateField()
    created = models.DateTimeField(default=timezone.now)

    @classmethod
    def get_latest_rates(cls):
        return (
            cls.objects.prefetch_related("target_currency")
            .order_by("target_currency__code", "-date")
            .distinct("target_currency__code")
        )

    def __str__(self):
        return f"{self.target_currency.code} | {self.rate} | {self.date}"

    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
