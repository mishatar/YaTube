from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import settings

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.permission_denied'
handler403csrf = 'core.views.csrf_failure'
handler500 = 'core.views.server_error'

urlpatterns = [
    path('', include('posts.urls', namespace='posts')),
    path('about/', include('about.urls', namespace='about')),
    path('auth/', include('users.urls', namespace='users')),
    path('auth/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
