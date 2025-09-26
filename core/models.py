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
    name = models.CharField(verbose_name='Название букета', max_length=50, unique=True)
    image = models.ImageField(verbose_name='Изображение букета', upload_to='bouquets/', blank=True)
    price = models.PositiveIntegerField(verbose_name='Цена', default=0, validators=[MinValueValidator(1)])
    description = models.TextField(verbose_name='Описание', blank=True)
    composition = models.TextField(verbose_name='Состав', blank=True)
    occasion = models.CharField(verbose_name='Повод', max_length=50, choices=OCCASIONS, default='no_occasion')
    budget = models.CharField(verbose_name='Бюджет', max_length=50, choices=BUDGETS, default='1000_5000')
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Букет'
        verbose_name_plural = 'Букеты'


class Customer(models.Model):
    first_name = models.CharField(verbose_name='Имя', max_length=50)
    last_name = models.CharField(verbose_name='Фамилия', max_length=50, blank=True)
    phone_number = PhoneNumberField(verbose_name='Номер телефона')
    def __str__(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()
    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Florist(models.Model):
    name = models.CharField(verbose_name='Имя флориста', max_length=100)
    phone_number = PhoneNumberField(verbose_name='Номер телефона', blank=True)
    telegram_chat_id = models.CharField(verbose_name='Telegram Chat ID', max_length=50, blank=True, help_text='Для уведомлений о заявках')
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Флорист'
        verbose_name_plural = 'Флористы'


class Courier(models.Model):
    name = models.CharField(verbose_name='Имя курьера', max_length=100)
    phone_number = PhoneNumberField(verbose_name='Номер телефона', blank=True)
    telegram_chat_id = models.CharField(verbose_name='Telegram Chat ID', max_length=50, blank=True, help_text='Для уведомлений о заказах')
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Курьер'
        verbose_name_plural = 'Курьеры'


class Order(models.Model):
    customer = models.ForeignKey(Customer, verbose_name='Покупатель', on_delete=models.CASCADE)
    bouquet = models.ForeignKey(Bouquet, verbose_name='Букет', related_name='orders', on_delete=models.CASCADE)
    courier = models.ForeignKey(Courier, verbose_name='Курьер', on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.CharField(verbose_name='Адрес доставки', max_length=256)
    delivery_time = models.CharField(verbose_name='Время доставки', max_length=30)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    def __str__(self):
        return f'{self.bouquet} для {self.customer}'
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class Consultation(models.Model):
    customer = models.ForeignKey(Customer, verbose_name='Покупатель', on_delete=models.SET_NULL, null=True, blank=True)
    florist = models.ForeignKey(Florist, verbose_name='Флорист', on_delete=models.SET_NULL, null=True, blank=True, help_text='Флорист, которому назначена заявка')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    def __str__(self):
        return f'Заявка от {self.customer or "Неизвестно"}'
    class Meta:
        verbose_name = 'Заявка на консультацию'
        verbose_name_plural = 'Заявки на консультацию'


class Payment(models.Model):
    order = models.OneToOneField(Order, verbose_name='Заказ', on_delete=models.CASCADE)
    payment_id = models.CharField(verbose_name='ID платежа', max_length=36, unique=True)
    status = models.CharField(verbose_name='Статус', max_length=50, default='pending')
    amount = models.DecimalField(verbose_name='Сумма', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    def __str__(self):
        return f'Платёж для заказа {self.order.id} ({self.status})'
    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'