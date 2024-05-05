from django.conf import settings
from django.http import HttpResponseRedirect
from django.db import models
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView

from django.views.generic.list import ListView

from django.urls import reverse_lazy

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Listing, Message, Utilities, Amenity, Feature

from django.forms.models import inlineformset_factory
from .forms import CreateListingForm, AmenityFormSet, FeatureFormSet, UtilitiesForm, ReviewListingForm, \
    UpdateListingForm, AmenityForm, FeatureForm

import rules
from rules.contrib.views import PermissionRequiredMixin

from .filters import ListingFilter

import requests


# Create your views here.
@login_required
def home(request):
    is_app_administrator = rules.test_rule('is_admin', request.user)

    listings = Listing.objects.filter(is_approved=True, is_hidden=False)

    # filtering - look for filtering paramters in url
    # gets all of the listings and applies applicable filters
    listing_filter = ListingFilter(request.GET, queryset=listings)
    listings = listing_filter.qs

    # listings' marker JavaScript code
    serialized_markers = [
        listing.get_marker_js() for listing in listings
    ]

    # marker info windows JavaScript code to context
    serialized_info_windows = [
        listing.get_info_window_js() for listing in listings
    ]

    context = {
        "is_app_administrator": is_app_administrator,
        "markers_json": serialized_markers,
        "info_windows": serialized_info_windows,
        "listings": listings,
        "filter": listing_filter,
        "key": settings.GOOGLE_API_KEY,
    }

    return render(request, "deploytest/home.html", context)


@login_required
def dashboard(request):
    is_app_administrator = rules.test_rule('is_admin', request.user)
    return render(
        request,
        "deploytest/dashboard.html",
        context={
            'is_admin': is_app_administrator,
        }
    )


class CreateListingView(LoginRequiredMixin, CreateView):
    form_class = CreateListingForm
    template_name = "deploytest/create_listing.html"
    success_url = reverse_lazy("home")

    @staticmethod
    def are_formsets_valid(formsets):
        valid = True
        for formset in formsets:
            valid = valid and formset.is_valid()

        return valid

    # Returns place id for listing address, empty string if no id can be found
    @staticmethod
    def get_place_id(address):
        address = address.replace(' ', '%20')  # make sure there are no blank spaces for the URL
        place_id_request_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=" + address + \
                               "&inputtype=textquery&fields=place_id&key=" + settings.GOOGLE_API_KEY
        response = requests.get(place_id_request_url).json()

        place_id = ''
        if response['status'] == "OK":
            place_id = response['candidates'][0]['place_id']

        return place_id

    def get_context_data(self, **kwargs):
        context = super(CreateListingView, self).get_context_data(**kwargs)

        if self.request.POST:
            context['amenity_formset'] = AmenityFormSet(self.request.POST, prefix='amenities')
            context['feature_formset'] = FeatureFormSet(self.request.POST, prefix='features')
            context['utility_form'] = UtilitiesForm(self.request.POST)
        else:
            context['amenity_formset'] = AmenityFormSet(prefix='amenities')
            context['feature_formset'] = FeatureFormSet(prefix='features')
            context['utility_form'] = UtilitiesForm()

        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        amenity_formset = AmenityFormSet(self.request.POST, prefix='amenities')
        feature_formset = FeatureFormSet(self.request.POST, prefix='features')
        utility_form = UtilitiesForm(self.request.POST)

        formsets = []
        formsets.append(amenity_formset)
        formsets.append(feature_formset)

        if form.is_valid() and utility_form.is_valid() and self.are_formsets_valid(formsets):
            return self.form_valid(form, formsets, utility_form)
        else:
            return self.form_invalid(form, formsets, utility_form)

    def form_valid(self, form, formsets, utilities_form):
        form.instance.author = self.request.user
        form.instance.utilities = utilities_form.save()
        self.object = form.save()
        self.object.place_id = self.get_place_id(self.object.address.raw)

        self.object.listing_type = form.cleaned_data['listing_type']
        self.object.save()

        for formset in formsets:
            set = formset.save(commit=False)

            for i in set:
                i.listing = self.object
                i.save()

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formsets, utilities_form):
        return self.render_to_response(
            self.get_context_data(form=form,
                                  formsets=formsets,
                                  utilities_form=utilities_form
                                  )
        )


class ListingDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Listing
    permission_required = "deploytest.view_listing"
    template_name = "deploytest/listing_detail.html"

    def get_photo_references(self, place_id):
        photos_request_url = "https://maps.googleapis.com/maps/api/place/details/json?fields=name%2Cphotos&place_id=" + place_id + \
                             "&key=" + settings.GOOGLE_API_KEY
        photos_response = requests.get(photos_request_url).json()
        photo_references = []

        if 'result' in photos_response and 'photos' in photos_response['result']:
            for photo in photos_response['result']['photos']:
                photo_references.append(photo['photo_reference'])

        return photo_references

    def make_photo_src_from_reference(self, reference):
        src = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference=" + reference + \
              "&key=" + settings.GOOGLE_API_KEY

        return src

    def get_context_data(self, **kwargs):
        place_id = self.get_object().place_id

        photo_srcs = []
        if place_id != '':
            photo_references = self.get_photo_references(place_id)
            for reference in photo_references:
                src = self.make_photo_src_from_reference(reference)
                photo_srcs.append(src)

        context = super(ListingDetailView, self).get_context_data(**kwargs)
        context['key'] = settings.GOOGLE_API_KEY
        context['photo_srcs'] = photo_srcs

        utilities = self.get_object().utilities
        if utilities:
            provided_utilities = [field for field in Utilities._meta.get_fields()
                                  if isinstance(field, models.BooleanField) and getattr(utilities, field.name)
                                  ]
            context['provided_utilities'] = provided_utilities

        return context


class UpdateListingView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Listing
    form_class = UpdateListingForm
    permission_required = 'deploytest.update_listing'
    template_name = 'deploytest/update_listing.html'
    success_url = reverse_lazy("manageable_listings")

    def get_context_data(self, **kwargs):
        if not hasattr(self, 'object'):
            self.object = self.get_object()

        context = super(UpdateListingView, self).get_context_data(**kwargs)

        initital_amenities = self.get_object().amenity_set.count()
        AmenityFormSet = inlineformset_factory(Listing, Amenity, form=AmenityForm, fields=['amenity'],
                                               extra=initital_amenities, can_delete=False)

        initital_features = self.get_object().feature_set.count()
        FeatureFormSet = inlineformset_factory(Listing, Feature, form=FeatureForm, fields=['feature'],
                                               extra=initital_features, can_delete=False)

        if self.request.POST:
            context['amenity_formset'] = AmenityFormSet(self.request.POST, prefix='amenities')
            context['feature_formset'] = FeatureFormSet(self.request.POST, prefix='features')
            context['utility_form'] = UtilitiesForm(self.request.POST)
        else:
            context['amenity_formset'] = AmenityFormSet(prefix='amenities', initial=[{'amenity': x.amenity} for x in
                                                                                     self.get_object().amenity_set.all()])
            context['feature_formset'] = FeatureFormSet(prefix='features', initial=[{'feature': x.feature} for x in
                                                                                    self.get_object().feature_set.all()])
            context['utility_form'] = UtilitiesForm(initial=self.get_object().utilities.__dict__)

        return context

    def post(self, request, *args, **kwargs):
        form = UpdateListingForm(request.POST, instance=self.get_object())

        amenity_formset = AmenityFormSet(self.request.POST, prefix='amenities')
        feature_formset = FeatureFormSet(self.request.POST, prefix='features')
        utility_form = UtilitiesForm(self.request.POST)

        formsets = []
        formsets.append(amenity_formset)
        formsets.append(feature_formset)

        if form.is_valid() and utility_form.is_valid() and CreateListingView.are_formsets_valid(formsets):
            return self.form_valid(form, formsets, utility_form)
        else:
            return self.form_invalid(form, formsets, utility_form)

    def form_valid(self, form, formsets, utilities_form):
        form.instance.utilities = utilities_form.save()
        self.object = form.save()
        # In case address was changed
        self.object.place_id = CreateListingView.get_place_id(self.object.address.raw)

        self.object.listing_type = form.cleaned_data['listing_type']
        self.object.save()

        self.get_object().amenity_set.all().delete()
        self.get_object().feature_set.all().delete()
        for formset in formsets:
            set = formset.save(commit=False)

            for i in set:
                i.listing = self.object
                i.save()

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, formsets, utilities_form):
        return self.render_to_response(
            self.get_context_data(form=form,
                                  formsets=formsets,
                                  utilities_form=utilities_form
                                  )
        )


class UpdateListingsListView(LoginRequiredMixin, ListView):
    model = Listing
    template_name = 'deploytest/update_listings_list.html'

    def get_context_data(self, **kwargs):
        context = super(UpdateListingsListView, self).get_context_data(**kwargs)

        approved_listings = []
        denied_listings = []  
        awaiting_approval_listings = []

        for listing in self.get_queryset():
            if listing.is_approved:
                approved_listings.append(listing)
            elif listing.is_reviewed:
                denied_listings.append(listing)
            else:
                awaiting_approval_listings.append(listing)

        context['approved_listings'] = approved_listings
        context['denied_listings'] = denied_listings
        context['awaiting_approval_listings'] = awaiting_approval_listings

        return context
    
    def get_queryset(self):
        return Listing.objects.filter(
            author=self.request.user
        )


class ModerateListingsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Listing
    permission_required = 'deploytest.review_listing'
    template_name = 'deploytest/moderate_listings_list.html'


class ModerateListingView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Listing
    fields = ["is_approved",
              "is_reviewed",
              "is_hidden"]
    permission_required = 'deploytest.review_listing'
    template_name = 'deploytest/moderate_listing.html'
    success_url = reverse_lazy("admin_all_listings")


class ReviewListingsListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Listing
    permission_required = 'deploytest.review_listing'
    template_name = 'deploytest/review_listings_list.html'

    def get_queryset(self):
        return Listing.objects.filter(
            is_reviewed=False
        )


class ReviewListingView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Listing
    form_class = ReviewListingForm
    permission_required = 'deploytest.review_listing'
    template_name = "deploytest/review_listing.html"
    success_url = reverse_lazy("admin_listings_pending_review")

    # pass the user (admin) who is submitting the review to the form
    def form_valid(self, form):
        form.set_author(self.request.user)
        return super().form_valid(form)


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "deploytest/messages.html"
    # context_object_name 'message' shadows bootstrap's message
    context_object_name = 'listing_messages'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(recipient=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_app_administrator'] = self.request.user.groups.filter(name='Administrator').exists()
        return context


@login_required
def clear_messages(request):
    user_msgs = Message.objects.filter(recipient=request.user)
    for msg in user_msgs:
        msg.delete()

    return redirect('messages')
