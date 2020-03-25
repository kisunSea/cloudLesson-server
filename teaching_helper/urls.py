from django.conf.urls import url, include
from django.contrib import admin

# routing distribution

urlpatterns = [
    url('^admin/', admin.site.urls),

    # WeChat applet
    url('^api/(?P<version>\w+)/wx_client/', include('wx_client.wx_urls', namespace='wx')),

    # Browser client
    url('^api/(?P<version>\w+)/browser_client/', include('browser_client.browser_urls', namespace='browser')),
]
