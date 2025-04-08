from django.urls import path
from user import views

urlpatterns = [
    path('', views.UserList.as_view(), name='user-list'),
    path('me', views.UserDetail.as_view(), name='user-detail')


]
