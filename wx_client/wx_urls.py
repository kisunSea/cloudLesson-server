from django.conf.urls import url
from wx_client import views

app_name = 'wx_client'

urlpatterns = [

    # GET
    url(r'^generate_code/$', views.LessonCodeAPIView.as_view()),

    # POST    face feature record
    url(r'^face_feature/record$', views.FaceProxy.as_view()),

    # POST    register an user
    url(r'^$', views.UserRegister.as_view(), name='register'),

    # GET     get information of the user who registered
    # PUT     update information of the user who registered
    # DELETE  delete an user
    url(r'^user$', views.UserInfoView.as_view(), name='user'),

    # GET     get classifies of subjects
    url(r'^lesson/subjects-classifies$', views.SubjectsClassifiesView.as_view()),

    # GET     get information: lessons created or joined by user,
    url(r'^lesson/$', views.LessonView.as_view()),

    # GET     get overview-information of page named `lesson-index`
    url(r'^lesson-index/overview/$', views.LessonIndexPageOverview.as_view()),
]
