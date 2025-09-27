from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Сумма заказа'),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачено'), ('failed', 'Ошибка оплаты')], default='pending', max_length=20, verbose_name='Статус оплаты'),
        ),
        migrations.AddField(
            model_name='order',
            name='yookassa_payment_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Id оплаты'),
        ),
    ]
