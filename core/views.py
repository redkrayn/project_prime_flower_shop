from django.shortcuts import render
from .models import Bouquet

def index(request):
    recommended = Bouquet.objects.all()[:3]
    return render(request, "index.html", {"recommended": recommended})

def catalog(request):
    bouquets = Bouquet.objects.all()
    return render(request, "catalog.html", {"bouquets": bouquets})

def order(request):
    return render(request, "order.html")

def order_step(request):
    return render(request, "order-step.html")

def consultation(request):
    return render(request, "consultation.html")

def quiz(request):
    return render(request, "quiz.html")

def quiz_step(request):
    return render(request, "quiz-step.html")

def result(request):
    return render(request, "result.html")
