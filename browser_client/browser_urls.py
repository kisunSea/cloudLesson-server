from django.conf.urls import url
from browser_client import views

app_name = 'browser_client'

urlpatterns = [

    # GET    get login page
    # POST   login
    url(r'^login$', views.LoginView.as_view(), name='login'),

]
