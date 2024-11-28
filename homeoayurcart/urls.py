"""homeoayurcart URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path,include
from ecommerce.views import index,product_details,update_cart,change_currency,toggle_wishlist,wishlist_view,cart,order_confirmation,past_orders,order_tracking,user_profile,search,get_address_details,checkout
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='home'),
    path('checkout/', checkout, name='checkout'),
    path('product_details/<int:product_id>/', product_details, name='product_details'),
    path('cart/', cart, name='cart'),
    path('update-cart/', update_cart, name='update_cart'),
    path('change-currency/', change_currency, name='change_currency'),  # Example URL pattern for changing currency
    path('toggle-wishlist/', toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('accounts/', include('allauth.urls')),  # Add this line
    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
    path('past-orders/', past_orders, name='past_orders'),
    path('order-tracking/<int:order_id>/', order_tracking, name='order_tracking'),
    path('profile/', user_profile, name='user_profile'),
    path('search/',search,name='search' ),
    path('get-address-details/', get_address_details, name='get_address_details'),

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)