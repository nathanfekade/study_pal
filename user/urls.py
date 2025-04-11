from django.urls import path
from user import views

urlpatterns = [
    path('signup/', views.UserList.as_view(), name='user-list'),
    path('edituser/', views.UserDetail.as_view(), name='user-detail')


]
