from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from store.views import (
    register,
    home,
    add_to_cart,
    cart,
    increase_quantity,
    decrease_quantity,
    remove_from_cart,
    checkout,
    my_orders,
    user_login,
    user_logout,
    product_detail,
    add_to_wishlist,
    wishlist,
    remove_from_wishlist,
    profile,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),

    path('register/', register, name='register'),


    path(
        'login/',
        user_login,
        name='login'
    ),

    path(
        'logout/',
        user_logout,
        name='logout'
    ),

    path('profile/', profile, name='profile'),
    
    

    path(
        'cart/add/<int:product_id>/',
        add_to_cart,
        name='add_to_cart'
    ),

    path(
        'cart/',
        cart,
        name='cart'
    ),

    path(
        'cart/increase/<int:item_id>/',
        increase_quantity,
        name='increase_quantity'
    ),

    path(
        'cart/decrease/<int:item_id>/',
        decrease_quantity,
        name='decrease_quantity'
    ),

    path(
    'cart/remove/<int:item_id>/',
    remove_from_cart,
    name='remove_from_cart'
),

path(
    'checkout/',
    checkout,
    name='checkout'
),

path(
    'orders/',
    my_orders,
    name='my_orders'
),


path(
    'product/<int:product_id>/',
    product_detail,
    name='product_detail'
),

path(
    'wishlist/add/<int:product_id>/',
    add_to_wishlist,
    name='add_to_wishlist'
),

path(
    'wishlist/',
    wishlist,
    name='wishlist'
),

path(
    'wishlist/remove/<int:product_id>/',
    remove_from_wishlist,
    name='remove_from_wishlist'
),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )