from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
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
    bouquets = Bouquet.objects.all().order_by('id')  
    paginator = Paginator(bouquets, 6)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'catalog.html', {'page_obj': page_obj})


def bouquet_detail(request, bouquet_id):
    bouquet = get_object_or_404(Bouquet, id=bouquet_id)
    return render(request, 'card.html', {'bouquet': bouquet})


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
    consultation = Consultation.objects.create(
        first_name=first_name,
        phone_number=phone_number
    )
    consultation.save()
    send_msg_to_florist(first_name, phone_number, consultation.created_at)
    return render(request, 'index.html')


def quiz(request):
    return render(request, "quiz.html", {
        "occasions": Bouquet.OCCASIONS
    })


def quiz_step(request):
    occasion = request.GET.get("occasion")
    if occasion:
        request.session['quiz_occasion'] = occasion
        return redirect('quiz_step')
    return render(request, "quiz-step.html", {"budgets": Bouquet.BUDGETS})


def result(request):
    budget = request.GET.get("budget")
    if budget:
        request.session['quiz_budget'] = budget
        return redirect('result')

    found_bouquet = Bouquet.objects.filter(
        occasion=request.session.get('quiz_occasion'),
        budget=request.session.get('quiz_budget')
    ).order_by('?').first()
    if not found_bouquet:
        found_bouquet = Bouquet.objects.first()

    bouquet = {
        "id": found_bouquet.id,
        "name": found_bouquet.name,
        "price": found_bouquet.price,
        "description": found_bouquet.description,
        "composition": found_bouquet.composition,
        "image": found_bouquet.image
    }

    request.session['quiz_results'] = {
        "occasion": request.session.get('quiz_occasion'),
        "budget": request.session.get('quiz_budget'),
        "bouquet_id": found_bouquet.id,
        "bouquet_name": found_bouquet.name
    }
    print(request.session['quiz_results'])
    return render(request, "result.html", {"bouquet": bouquet})