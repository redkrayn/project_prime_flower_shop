from django.shortcuts import render, get_object_or_404
from .models import Bouquet


def index(request):
    recommended = Bouquet.objects.all()[:3]
    return render(request, "index.html", {"recommended": recommended})


def order(request):
    return render(request, 'order.html')


def order_step(request):
    return render(request, 'order-step.html')


def catalog(request):
    bouquets = Bouquet.objects.all()  
    return render(request, 'catalog.html', {'bouquets': bouquets})


def consultation(request):
    return render(request, 'consultation.html')


def quiz(request):
    return render(request, 'quiz.html')


def quiz_step(request):
    return render(request, 'quiz-step.html')


def result(request, pk):
    bouquet = get_object_or_404(Bouquet, pk=pk)  
    return render(request, 'result.html', {'bouquet': bouquet})
