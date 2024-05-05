from django.conf import settings
from django.db import models
import requests
from django.core.validators import MinValueValidator
from address.models import AddressField
from django.urls import reverse
from rules.contrib.models import RulesModel

from .rules import p_is_listing_author, p_is_listing_hidden, p_is_listing_approved, p_is_admin
import datetime


# Included Utilities
class Utilities(models.Model):
    gas = models.BooleanField(default=False, verbose_name="Gas")
    water = models.BooleanField(default=False, verbose_name="Water")
    heat = models.BooleanField(default=False, verbose_name="Heat")
    trash = models.BooleanField(default=False, verbose_name="Trash")
    sewer = models.BooleanField(default=False, verbose_name="Sewer")
    electricity = models.BooleanField(default=False, verbose_name="Electricity")
    internet = models.BooleanField(default=False, verbose_name="Internet")
    security = models.BooleanField(default=False, verbose_name="Security")
    cable = models.BooleanField(default=False, verbose_name="Cable")
    phone = models.BooleanField(default=False, verbose_name="Phone")


class Listing(RulesModel):
    """Constants"""
    MIN_NUM_BEDS = 0
    MIN_NUM_BATHS = 0
    MIN_RENT = 0
    MIN_SQUARE_FEET = 0

    """Fields"""
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    utilities = models.OneToOneField(Utilities, null=True, on_delete=models.CASCADE)
    apartment_name = models.CharField(max_length=100)
    apartment_description = models.TextField()
    listing_description = models.TextField()
    listing_type = models.CharField(max_length=50)
    lease_start = models.DateField(default=datetime.date.today)
    lease_end = models.DateField(default=datetime.date.today)
    address = AddressField()
    place_id = models.TextField(default="")
    parking = models.BooleanField()
    square_feet = models.IntegerField(
        verbose_name="Square feet",
        validators=[MinValueValidator(MIN_SQUARE_FEET)],
        default=1
    )
    num_beds = models.IntegerField(
        verbose_name="Number of beds",
        validators=[MinValueValidator(MIN_NUM_BEDS)],
        default=1,
    )
    num_baths = models.IntegerField(
        verbose_name="Number of bathrooms",
        validators=[MinValueValidator(MIN_NUM_BATHS)],
        default=1,
    )
    rent_per_month = models.IntegerField(validators=[MinValueValidator(MIN_RENT)])

    # whether an admin has approved this listing
    is_approved = models.BooleanField(default=False)

    # whether an admin has reviewed this listing (approve or deny)
    # should be set to False when listing is created or updated
    is_reviewed = models.BooleanField(default=False)

    # whether the creator of this listing has hidden it
    is_hidden = models.BooleanField(default=False)

    class Meta:
        rules_permissions = {
            "view": (p_is_listing_approved & (~p_is_listing_hidden)) | p_is_admin | p_is_listing_author,
            "update": p_is_admin | p_is_listing_author,
            "review": p_is_admin,
        }

    def get_marker_js(self):
        if self.address:

            base_url = 'https://maps.googleapis.com/maps/api/geocode/json'

            params = {
                'address': self.address,
                'key': settings.GOOGLE_API_KEY
            }

            # make the request
            response = requests.get(base_url, params=params)

            # if the request was successful, parse the response
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'OK':
                    location = data['results'][0]['geometry']['location']
                    latitude = location['lat']
                    longitude = location['lng']
                    return f'addMarker({latitude}, {longitude}, "{self.apartment_name}");'

        return ""

    def get_info_window_js(self):
        if self.address:
            # get the url for the listing detail page
            listing_url = reverse('listing_detail', args=[self.id])

            # create the content for the info window
            info_content = (
                f"<h3>{self.apartment_name}</h3>"
                f"<p><b>Address:</b> {self.address}</p>"
                f"<p><b>Number of Beds:</b> {self.num_beds} &nbsp;&nbsp;&nbsp; <b>Number of Baths:</b> {self.num_baths}</p>"
                f"<p><b>Rent per Month:</b> ${self.rent_per_month}</p>"
                f"<p><a href='{listing_url}'>View Listing</a></p>"
            )

            info_content = info_content.replace("'", r"\'")

            return f'addInfoWindow("{info_content}");'

        return ""
    

# Community Amenities
class Amenity(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    amenity = models.CharField(max_length=50)


# Apartment Features
class Feature(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    feature = models.CharField(max_length=50)


class Message(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               limit_choices_to={'groups__name': 'Administrator'},
                               on_delete=models.CASCADE,
                               related_name='authored_messages')
    message = models.TextField()
    
    def __str__(self):
        return f"From: {self.author.username} - To: {self.recipient.username}"