from django.shortcuts import render, get_object_or_404
from .models import Bouquet


def index(request):
<<<<<<< HEAD
    return render(request, 'index.html')
=======
    recommended = Bouquet.objects.all()[:3]
    return render(request, "index.html", {"recommended": recommended})


def catalog(request):
    bouquets = Bouquet.objects.all()
    return render(request, "catalog.html", {"bouquets": bouquets})
>>>>>>> 5a083c8b54f502f31e3f2266ac7eae15bc590958



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

<<<<<<< HEAD
def result(request, pk):
    bouquet = get_object_or_404(Bouquet, pk=pk)  
    return render(request, 'result.html', {'bouquet': bouquet})
=======


def result(request):
    return render(request, "result.html")
>>>>>>> 5a083c8b54f502f31e3f2266ac7eae15bc590958
