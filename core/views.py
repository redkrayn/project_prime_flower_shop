from django.shortcuts import render, redirect, get_object_or_404

from .models import Bouquet, Customer, Order, Courier, Consultation
from .send_msg_tg import send_msg_to_florist



def index(request):
    recommended = Bouquet.objects.all()[:3]
    return render(request, "index.html", {"recommended": recommended})


def order(request):
    bouquets = Bouquet.objects.all()
    delivery_times = [
        'Как можно скорее', 'с 10:00 до 12:00', 'с 12:00 до 14:00',
        'с 14:00 до 16:00', 'с 16:00 до 18:00', 'с 18:00 до 20:00'
    ]
    if request.method == 'POST':
        bouquet_id = request.POST.get('bouquet')
        first_name = request.POST.get('first_name')
        phone_number = request.POST.get('phone_number')
        delivery_address = request.POST.get('delivery_address')
        delivery_time = request.POST.get('delivery_time')

    customer, created = Customer.objects.get_or_create(
        first_name=first_name,
        phone_number=phone_number,
        defaults={'last_name': ''}
    )
    # available_couriers = Courier.objects.all()
    # if available_couriers:
    #     courier = random.choice(available_couriers)
    # ДОПИЛИТЬ ЛОГИКУ ВЫБОРА КУРЬЕРА
    order = Order(
        customer=customer,
        bouquet_id=bouquet_id,# ПОКА null=True, blank=True В МОДЕЛИ ORDER
        delivery_address=delivery_address,
        delivery_time=delivery_time,
        courier=None
    )
    order.save()
    request.session['order_id'] = order.id
    
    return render(request, 'order.html', {
        'bouquets': bouquets,
        'delivery_times': delivery_times
    })


def order_step(request):
    return render(request, 'order-step.html')


def catalog(request):
    bouquets = Bouquet.objects.all()  
    return render(request, 'catalog.html', {'bouquets': bouquets})


def consultation(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        phone_number = request.POST.get('phone_number')

    consultation = Consultation.objects.create(
        first_name=first_name,
        phone_number=phone_number
    )
    consultation.save()
    send_msg_to_florist(first_name, phone_number, consultation.created_at)
    return render(request, 'index.html')


def quiz(request):
    return render(request, 'quiz.html')


def quiz_step(request):
    return render(request, 'quiz-step.html')


def result(request, pk):
    bouquet = get_object_or_404(Bouquet, pk=pk)  
    return render(request, 'result.html', {'bouquet': bouquet})
