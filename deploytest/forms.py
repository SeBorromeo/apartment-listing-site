from django import forms
from django.forms.models import inlineformset_factory
from address.models import Address

from .models import Listing, Amenity, Feature, Utilities
from .models import Message

NON_USER_EDITABLE_FIELDS = ('author', 'is_approved', 'is_reviewed', 'utilities', 'place_id')
LISTING_TYPES = (('Looking to Sublet over Summer', 'Looking to Sublet over Summer'),
                     ('Looking to Sublet over Winter', 'Looking to Sublet over Winter'),
                     ('Looking to Give over Lease', 'Looking to Give over Lease'),
                     ('Looking to Sublet', 'Looking to Sublet'),
                     ('Looking for Roommate', 'Looking for Roommate'), ('Lease', 'Lease'))

class CreateListingForm(forms.ModelForm):
    listing_type = forms.ChoiceField(choices=LISTING_TYPES)

    class Meta:
        model = Listing
        exclude = NON_USER_EDITABLE_FIELDS
        widgets = {
            "lease_start": forms.SelectDateWidget(),
            "lease_end": forms.SelectDateWidget(),
        }


class AmenityForm(forms.ModelForm):
    class Meta:
        model = Amenity
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AmenityForm, self).__init__(*args, **kwargs)
        self.fields['amenity'].widget = forms.TextInput(attrs={
            'placeholder': 'Enter Amenity'})


AmenityFormSet = inlineformset_factory(Listing, Amenity, form=AmenityForm, fields=['amenity'], extra=1,
                                       can_delete=False)


class FeatureForm(forms.ModelForm):
    class Meta:
        model = Feature
        fields = '__all__'


FeatureFormSet = inlineformset_factory(Listing, Feature, form=FeatureForm, fields=['feature'], extra=1,
                                       can_delete=False)


class UtilitiesForm(forms.ModelForm):
    class Meta:
        model = Utilities
        fields = '__all__'


class ReviewListingForm(forms.ModelForm):
    review_feedback = forms.CharField(required=False, max_length=300)

    class Meta:
        model = Listing
        fields = ('is_approved',)

    def make_review_message(self, approved: bool, name):
        feedback = self.cleaned_data["review_feedback"]
        return (
            f"Listing \"{name}\" {'Approved' if approved else 'Rejected'}"
            f"{f' - Feedback: {feedback}' if feedback else ''}"
        )

    def save(self, commit=True):
        listing = super().save(commit=False)
        listing.is_reviewed = True

        msg = Message(
            recipient=listing.author,
            author=self.author,
            message=self.make_review_message(listing.is_approved, listing.apartment_name)
        )
        if commit:
            listing.save()
            msg.save()
        return listing

    def set_author(self, user):
        self.author = user


class UpdateListingForm(forms.ModelForm):
    no_review_fields = {"is_hidden"}
    
    listing_type = forms.ChoiceField(choices=LISTING_TYPES)
    
    class Meta:
        model = Listing
        exclude = NON_USER_EDITABLE_FIELDS
        widgets = {
            "lease_start": forms.SelectDateWidget(),
            "lease_end": forms.SelectDateWidget(),
        }

    def save(self, commit=True):
        listing = super().save(commit=False)

        # listing changes should be re-approved, to prevent
        # malicious actors from getting a listing approved
        # and then updating it to violate TOS or something

        # for some reason, self.changed_data includes fields that didn't actually change
        # specifically, we found that lease dates are reported changed when they don't change
        # prune those fields
        changed_data = set(field for field in self.changed_data if self[field].initial != self.cleaned_data[field])

        # address-specific workaround
        # for some reason, the initial data of an address field is its primary key
        # this breaks self.changed_data because the incoming cleaned data is the actual address,
        # even if the objects are the same. compare the raw addresses instead, so that if the
        # address is not updated, we won't trigger re-review
        initial_addr = Address.objects.get(pk=self["address"].initial)
        if 'address' in changed_data and initial_addr.raw == self.cleaned_data['address'].raw:
            changed_data.remove('address')

        # only require this re-approval if a field that actually
        # requires re-approval has been changed
        num_review_required_fields_changed = len(changed_data - UpdateListingForm.no_review_fields)
        if num_review_required_fields_changed > 0:
            listing.is_reviewed = False
            listing.is_approved = False

        if commit:
            listing.save()
        return listing
