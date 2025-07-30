from .models import Category

def menu_links(request):
    print("GOOD CONTExT ")
    links=Category.objects.all() 
    return dict(links=links)