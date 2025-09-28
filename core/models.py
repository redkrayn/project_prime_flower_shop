from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator


class Bouquet(models.Model):
    OCCASIONS = [
        ('wedding', 'Свадьба'),
        ('birthday', 'День рождения'),
        ('no_occasion', 'Без повода'),
        ('other', 'Другой повод'),
    ]
    BUDGETS = [
        ('up_to_1000', 'До 1000 рублей'),
        ('1000_5000', '1000-5000 рублей'),
        ('from_5000', 'От 5000'),
        ('any', 'Не имеет значения'),
    ]
    name = models.CharField(
        verbose_name='Название букета',
        max_length=50,
    )
    image = models.ImageField(
        verbose_name='Изображение букета',
        upload_to='bouquets/',
        blank=True
    )
    price = models.PositiveIntegerField(
        verbose_name='Цена',
        default=0,
        validators=[MinValueValidator(1)]
    )
    description = models.TextField(verbose_name='Описание', blank=True)
    composition = models.TextField(verbose_name='Состав', blank=True)
    occasion = models.CharField(
        verbose_name='Повод',
        max_length=50,
        choices=OCCASIONS,
        default='no_occasion'
    )
    budget = models.CharField(
        verbose_name='Бюджет',
        max_length=50,
        choices=BUDGETS,
        default='1000_5000'
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Букет'
        verbose_name_plural = 'Букеты'


class Customer(models.Model):
    first_name = models.CharField(verbose_name='Имя', max_length=50)
    phone_number = PhoneNumberField(verbose_name='Номер телефона', unique=True)

    def str(self):
        return f'{self.phone_number}'

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Florist(models.Model):
    name = models.CharField('Имя сотрудника', max_length=100)
    phone_number = PhoneNumberField('Номер телефона', blank=True)
    tg_chat_id = models.PositiveBigIntegerField(
        verbose_name='Чат ID сотрудника в Telegram',
        blank=True,
        null=True)
    is_active = models.BooleanField(verbose_name='Активен', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Курьер'
        verbose_name_plural = 'Курьеры'


class Courier(models.Model):
    name = models.CharField('Имя сотрудника', max_length=100)
    phone_number = PhoneNumberField('Номер телефона', blank=True)
    tg_chat_id = models.PositiveBigIntegerField(
        verbose_name='Чат ID сотрудника в Telegram',
        blank=True,
        null=True)
    is_active = models.BooleanField(verbose_name='Активен', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Курьеры'
        verbose_name = 'Курьер'


class Order(models.Model):
    ORDER_STATUS = [
        ('waiting_for_delivery', 'Ожидается доставка'),
        ('delivered', 'Доставлен'),
    ]
    customer = models.ForeignKey(
        Customer,
        verbose_name='Покупатель',
        on_delete=models.CASCADE
    )
    bouquet = models.ForeignKey(
        Bouquet,
        verbose_name='Букет',
        related_name='orders',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    courier = models.ForeignKey(
        Courier, verbose_name='Ответственный сотрудник',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=True,
    )
    status = models.CharField(
        verbose_name='Статус заказа',
        max_length=50,
        choices=ORDER_STATUS,
        default='waiting_for_delivery'
    )
    delivery_address = models.CharField(
        verbose_name='Адрес доставки',
        max_length=256
    )
    delivery_time = models.CharField(
        verbose_name='Время доставки',
        max_length=30
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    payment_status = models.CharField(
        verbose_name='Статус оплаты',
        max_length=20,
        choices=[
            ('pending', 'Ожидает оплаты'),
            ('paid', 'Оплачено'),
            ('failed', 'Ошибка оплаты')
        ],
        default='pending'
    )
    yookassa_payment_id = models.CharField(
        verbose_name='Id оплаты',
        max_length=100,
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        verbose_name='Сумма заказа',
        max_digits=10,
        decimal_places=2,
        default=0
    )
    is_counted = models.BooleanField(verbose_name='Заказ учтен в статистике', default=False)


class Consultation(models.Model):
    customer = models.ForeignKey(
        Customer,
        verbose_name='Покупатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    florist = models.ForeignKey(
        Florist, verbose_name='Флорист',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Флорист, которому назначена заявка'
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )

    def __str__(self):
        return f'Заявка от {self.customer or "Неизвестно"}'

    class Meta:
        verbose_name = 'Заявка на консультацию'
        verbose_name_plural = 'Заявки на консультацию'
