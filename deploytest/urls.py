from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("create_listing/", views.CreateListingView.as_view(), name="create_listing"),
    path("listing/<int:pk>/", views.ListingDetailView.as_view(), name="listing_detail"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/manage_listings/pending_review/", views.ReviewListingsListView.as_view(), name="admin_listings_pending_review"),
    path("dashboard/manage_listings/review_listing/<int:pk>/", views.ReviewListingView.as_view(), name="admin_review_listing"),
    path("dashboard/manage_listings/all_listings/", views.ModerateListingsListView.as_view(), name="admin_all_listings"),
    path("dashboard/manage_listings/moderate_listing/<int:pk>/", views.ModerateListingView.as_view(), name="admin_moderate_listing"),
    path("dashboard/manage_listings/update_listing/<int:pk>/", views.UpdateListingView.as_view(), name="update_listing"),
    path("dashboard/manage_listings/", views.UpdateListingsListView.as_view(), name="manageable_listings"),
    path("dashboard/messages/", views.MessageListView.as_view(), name="messages"),
    path("dashboard/messages/clear", views.clear_messages, name="clear_messages"),
]
