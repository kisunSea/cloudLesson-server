from django.conf.urls import url
from browser_client import views
from django.contrib.auth.decorators import login_required

app_name = 'browser_client'

urlpatterns = [

    # GET    get login page
    # POST   login
    url(r'^login$', views.LoginView.as_view(), name='login'),

    # GET    return index pageView
    url(r'^index$', login_required(views.UploadFile.as_view()), name='upload_file'),

    # GET    exit sys
    url(r'^exit$', views.ExitLogin.as_view(), name='exit'),

    # GET    download exam template
    url(r'^template$', views.ExamTemplateDownload.as_view(), name='download_t')
]
