from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# routing distribution

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # WeChat applet
    url(r'^api/(?P<version>\w+)/wx_client/', include('wx_client.wx_urls', namespace='wx')),

    # Browser client
    url(r'^api/(?P<version>\w+)/browser_client/', include('browser_client.browser_urls', namespace='browser')),
]

urlpatterns.extend(staticfiles_urlpatterns())