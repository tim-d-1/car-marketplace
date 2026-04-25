from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("auth/callback/", views.auth_callback_view, name="auth_callback"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/my-ads/", views.my_ads, name="my_ads"),
    path("profile/my-ads/toggle/<int:car_id>/", views.toggle_car_status, name="toggle_car_status"),
    path("profile/purchases/", views.purchase_history, name="purchase_history"),
    path("car/<int:car_id>/", views.car_detail, name="car_detail"),
    path("car/<int:car_id>/checkout/", views.checkout_view, name="checkout"),
    path("api/payment-success/", views.payment_success_api, name="payment_success_api"),
    path("api/confirm-delivery/", views.confirm_delivery_api, name="confirm_delivery_api"),
    path("api/cancel-order/", views.cancel_order_api, name="cancel_order_api"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/toggle/<int:car_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/read/<int:notification_id>/", views.mark_notification_read, name="mark_notification_read"),
    path("api/filter-options/", views.get_filter_options, name="get_filter_options"),
    path("add/", views.add_auto, name="add_auto"),
    path("car/<int:car_id>/edit/", views.edit_auto, name="edit_auto"),
    path("car/<int:car_id>/delete/", views.delete_auto, name="delete_auto"),
    path("admin-panel/users/", views.admin_users_list, name="admin_users_list"),
    path("admin-panel/users/<int:user_id>/", views.admin_user_detail, name="admin_user_detail"),
]
