from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json
from yookassa import Payment as YooPayment

from .models import Bouquet, Customer, Order, Consultation
from .yookassa_service import create_payment
from .send_msg_tg import send_msg_to_florist, send_msg_to_courier

from django.http import JsonResponse
from django.template.loader import render_to_string


def index(request):
    recommended = Bouquet.objects.all()[:3]
    return render(request, "index.html", {"recommended": recommended})


def order(request):
    bouquets = Bouquet.objects.all()
    bouquet_id = request.session.get('selected_bouquet_id')

    delivery_times = [
        'Как можно скорее', 'с 10:00 до 12:00', 'с 12:00 до 14:00',
        'с 14:00 до 16:00', 'с 16:00 до 18:00', 'с 18:00 до 20:00'
    ]
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        delivery_address = request.POST.get('delivery_address')
        delivery_time = request.POST.get('delivery_time')

        customer, created = Customer.objects.get_or_create(
            name=name,
            phone_number=phone_number,
        )

        bouquet = Bouquet.objects.get(id=bouquet_id)

        order = Order(
            customer=customer,
            bouquet_id=bouquet_id,
            delivery_address=delivery_address,
            delivery_time=delivery_time,
            amount=bouquet.price
        )
        order.save()

        return_url = request.build_absolute_uri(reverse('payment_success'))
        payment = create_payment(order, return_url)

        order.yookassa_payment_id = payment.id
        order.save()

        request.session['order_id'] = order.id
        return redirect(payment.confirmation.confirmation_url)

    return render(request, 'order.html', {
        'bouquets': bouquets,
        'delivery_times': delivery_times
    })


def payment_success(request):
    order_id = request.session.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        payment = YooPayment.find_one(order.yookassa_payment_id)

        if payment.status == 'succeeded':
            order.payment_status = 'paid'
            order.save()

            send_msg_to_courier(order)

            if 'order_id' in request.session:
                del request.session['order_id']

            bouquets = Bouquet.objects.all().order_by('id')
            paginator = Paginator(bouquets, 6)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
            return render(request, 'catalog.html', {'page_obj': page_obj})

        else:
            if 'order_id' in request.session:
                del request.session['order_id']
            return redirect('payment_failed')


def payment_failed(request):
    order_id = request.session.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        order.payment_status = 'failed'
        order.save()

    return render(request, 'payment_failed.html')


@csrf_exempt
def yookassa_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data['object']['id']

            order = Order.objects.get(yookassa_payment_id=payment_id)
            payment = YooPayment.find_one(payment_id)

            if payment.status == 'succeeded':
                order.payment_status = 'paid'
                order.save()

        except Exception as e:
            print(f"Error processing webhook: {e}")

    return HttpResponse(status=200)


def catalog(request):
    bouquets = Bouquet.objects.all()
    paginator = Paginator(bouquets, 6)  
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'catalog.html', {'page_obj': page_obj})


def load_more_bouquets(request):
    page = int(request.GET.get('page', 1))
    bouquets = Bouquet.objects.all()
    paginator = Paginator(bouquets, 6)  
    if page <= paginator.num_pages:
        page_obj = paginator.page(page)
        html = render_to_string('bouquets_partial.html', {'page_obj': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None
        })
    return JsonResponse({'html': '', 'has_next': False})


def bouquet_detail(request, bouquet_id):
    bouquet = get_object_or_404(Bouquet, id=bouquet_id)
    request.session['selected_bouquet_id'] = bouquet_id
    return render(request, 'card.html', {'bouquet': bouquet})


def consultation(request):
    occasion = request.GET.get("occasion")
    budget = request.GET.get("budget")
    quiz_results = None
    if occasion and budget:
        quiz_results = {"occasion": occasion, "budget": budget}

    if request.method == 'GET':
        return render(request, 'consultation.html')

    name = request.POST.get('name')
    phone_number = request.POST.get('phone_number')

    customer, created = Customer.objects.get_or_create(
        phone_number=phone_number,
        defaults={'name': name}
    )
    consultation = Consultation.objects.create(customer=customer)

    send_msg_to_florist(
        consultation=consultation,
        quiz_results=quiz_results
    )
    return redirect('index')



def quiz(request):
    return render(request, "quiz.html", {
        "occasions": Bouquet.OCCASIONS
    })


def quiz_step(request):
    occasion = request.GET.get("occasion")
    if not occasion:
        return redirect("quiz")

    return render(request, "quiz-step.html", {
        "budgets": Bouquet.BUDGETS,
        "occasion": occasion,
    })


def result(request):
    occasion = request.GET.get("occasion")
    budget = request.GET.get("budget")

    if not occasion or not budget:
        return redirect("quiz")

    found_bouquet = Bouquet.objects.filter(
        occasion=occasion,
        budget=budget
    ).order_by("?").first()

    if not found_bouquet:
        found_bouquet = Bouquet.objects.first()

    bouquet = {
        "id": found_bouquet.id,
        "name": found_bouquet.name,
        "price": found_bouquet.price,
        "description": found_bouquet.description,
        "composition": found_bouquet.composition,
        "image": found_bouquet.image,
    }

    return render(request, "result.html", {
        "bouquet": bouquet,
        "occasion": occasion,
        "budget": budget,
    })


def privacy_policy(request):
    return render(request, 'privacy_policy.html')