import json

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from yookassa import Payment as YooPayment

from .models import Bouquet, Customer, Order, Consultation
from .yookassa_service import create_payment
from .send_msg_tg import send_msg_to_florist, send_msg_to_courier


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

        if not all([name, phone_number, delivery_address, delivery_time]):
            return render(request, 'order.html', {
                'bouquets': bouquets,
                'delivery_times': delivery_times,
                'error': 'Пожалуйста, заполните все поля формы'
            })

        if not bouquet_id:
            return render(request, 'order.html', {
                'bouquets': bouquets,
                'delivery_times': delivery_times,
                'error': 'Букет не выбран. Пожалуйста, выберите букет.'
            })

        try:
            # Создаем или получаем клиента
            customer, created = Customer.objects.get_or_create(
                phone_number=phone_number,
                defaults={'name': name}
            )
            if not created and customer.name != name:
                customer.name = name
                customer.save()

            bouquet = get_object_or_404(Bouquet, id=bouquet_id)

            # Создаем заказ
            order = Order.objects.create(
                customer=customer,
                bouquet=bouquet,
                delivery_address=delivery_address,
                delivery_time=delivery_time,
                amount=bouquet.price
            )

            # Создаем платеж
            payment = create_payment(order, reverse('payment_result'))
            # Сохраняем id платежа
            order.yookassa_payment_id = payment.id
            order.save()

            # Сохраняем в сессии для последующей проверки
            request.session['order_id'] = order.id

            # Редирект на страницу подтверждения YooKassa
            return redirect(payment.confirmation.confirmation_url)

        except Exception as e:
            return render(request, 'order.html', {
                'bouquets': bouquets,
                'delivery_times': delivery_times,
                'error': f'Произошла ошибка при создании заказа: {str(e)}'
            })

    # GET-запрос — просто рендер формы
    return render(request, 'order.html', {
        'bouquets': bouquets,
        'delivery_times': delivery_times
    })


def payment_result(request):
    order_id = request.session.pop('order_id', None)

    if not order_id:
        return redirect('catalog')

    try:
        order = get_object_or_404(Order, id=order_id)
        payment = YooPayment.find_one(order.yookassa_payment_id)

        if payment.status == 'succeeded':
            order.payment_status = 'paid'
            order.save()
            request.session['payment_message'] = 'Заказ успешно оплачен!'
            return redirect('catalog')
        else:
            order.payment_status = 'failed'
            order.save()
            request.session['payment_message'] = 'Оплата отклонена, повторите попытку позднее...'
            return redirect('catalog')

    except Exception:
        request.session['payment_message'] = 'Неизвестная ошибка при оплате.'
        return redirect('catalog')


@csrf_exempt
def yookassa_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data['object']['id']
            order = get_object_or_404(Order, yookassa_payment_id=payment_id)
            payment = YooPayment.find_one(payment_id)

            if payment.status == 'succeeded' and order.payment_status != 'paid':
                order.payment_status = 'paid'
                order.save()
                send_msg_to_courier(order)
            elif payment.status in ['canceled', 'waiting_for_capture']:
                order.payment_status = 'failed'
                order.save()

        except Exception:
            return HttpResponse(status=500)

    return HttpResponse(status=200)


def catalog(request):
    bouquets = Bouquet.objects.all()
    paginator = Paginator(bouquets, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    if request.session.get('payment_message'):
        message = request.session.pop('payment_message', None)
        return render(
            request,
            'catalog.html',
            {
                'page_obj': page_obj,
                'message': message
            }
        )
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

    if not all([name, phone_number]):
        return render(request, 'consultation.html', {'error': 'Заполните все поля'})

    customer, created = Customer.objects.get_or_create(
        phone_number=phone_number,
        defaults={'name': name}
    )
    if not created and customer.name != name:
        customer.name = name
        customer.save()

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

    request.session['selected_bouquet_id'] = found_bouquet.id

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