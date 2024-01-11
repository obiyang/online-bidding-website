"""
URL configuration for group1_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView
from auctionHouse import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name='home'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile_with_username'),
    path('auction/<int:auction_id>/send_message/', views.send_message, name='send_message'),
    path('messages/', views.view_messages, name='view_messages'),
    path("__debug__/", include("debug_toolbar.urls")),
    path("auction/", views.AuctionListView.as_view(), name='auction'),
    path('auction/create/', views.AuctionCreateView.as_view(), name='auction_create'),
    path("auction/<int:pk>", views.AuctionDetailView.as_view(), name='auction_detail'),
    path('auctions/category/<int:category_id>/', views.auctions_by_category, name='auctions_by_category'),
    path('submit_rating/<int:auction_id>/', views.submit_rating, name='submit_rating'),
    path('payment/<int:auction_id>/', views.payment_view, name='payment_view'),
    path('shipping/<int:auction_id>/', views.shipping_view, name='shipping_view'),
    path('weekly_report/', views.weekly_report_view, name='weekly_report_view'),
    path('daily_report/', views.daily_report_view, name='daily_report_view'),
    path('chat/', views.chat, name='chat'),
    path('chat-bot/', views.chatbot_view, name='chat_bot'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

