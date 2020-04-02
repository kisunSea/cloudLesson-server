from django.conf.urls import url
from wx_client import views

app_name = 'wx_client'

urlpatterns = [

    # POST face feature record
    url(r'^face_feature/record$', views.FaceProxy.as_view()),

    # POST    register an user
    url(r'^$', views.UserRegister.as_view(), name='register'),

    # GET     get information of the user who registered
    # PUT     update information of the user who registered
    # DELETE  delete an user
    url('^user$', views.UserInfoView.as_view(), name='user'),


]
