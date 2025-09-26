from django.shortcuts import render, redirect, get_object_or_404

from .models import Bouquet, Customer, Order, Courier, Consultation
from .send_msg_tg import send_msg_to_florist, send_msg_to_courier



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
        
        courier = Courier.objects.filter(is_active=True).order_by('number_orders').first()

        order = Order(
            customer=customer,
            bouquet_id=bouquet_id,
            delivery_address=delivery_address,
            delivery_time=delivery_time,
            is_counted=True,
            courier=courier
        )
        order.save()

        courier.number_orders += 1
        courier.save()
        send_msg_to_courier(courier.name, 
                            customer.first_name, 
                            customer.phone_number, 
                            order.delivery_time)
        
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

    customer, created = Customer.objects.get_or_create(
            first_name=first_name,
            phone_number=phone_number,
            defaults={'last_name': ''}
        )

    consultation = Consultation.objects.create(
        customer=customer,
    )
    consultation.save()
    send_msg_to_florist(customer.first_name, customer.phone_number, consultation.created_at)
    return render(request, 'index.html')


def quiz(request):
    return render(request, "quiz.html", {
        "occasions": Bouquet.OCCASIONS
    })


def quiz_step(request):
    occasion = request.GET.get("occasion")
    return render(request, "quiz-step.html", {
        "occasion": occasion,
        "budgets": Bouquet.BUDGETS
    })


def result(request):
    # заглушка TODO: запрашивать букет из БД на основе GET параметров
    bouquet = {
        "name": "Летнее утро",
        "price": 3600,
        "description": "Этот букет передает атмосферу летнего утра в деревне. Букет создан из свежих полевых цветов, собранных вручную.",
        "composition": "Альстромерия белая, Эустома белая, Ромашка, Роза пионовидная",
        "image": "img/cardImg.jpg"
    }
    return render(request, "result.html", {"bouquet": bouquet})
