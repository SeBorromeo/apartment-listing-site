from django.test import TestCase
from django.urls import reverse

from .models import Listing, Message
from .forms import CreateListingForm, AmenityForm, ReviewListingForm, UpdateListingForm

from .filters import ListingFilter
from address.models import Address
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
import datetime

DEFAULT_LISTING_CONSTANTS = {
    "apartment_name": "test apt",
    "apartment_description": "a test apt",
    "listing_description": "a test apt",
    "listing_type": "Looking for Roommate",
    "lease_start": datetime.date(2023, 11, 12),
    "lease_end": datetime.date(2024, 11, 12),
    "address": "raw address",
    "place_id": "",
    "parking": "True",
    "square_feet": Listing.MIN_SQUARE_FEET,
    "num_beds": Listing.MIN_NUM_BEDS,
    "num_baths": Listing.MIN_NUM_BATHS,
    "rent_per_month": Listing.MIN_RENT,
    "is_approved": True,
    "is_reviewed": True,
    "is_hidden": False,
}


# Create your tests here.
class CreateListingFormTests(TestCase):
    def setUp(self) -> None:
        self.default_data = DEFAULT_LISTING_CONSTANTS.copy()

    def test_create_too_few_num_beds(self):
        """
        A creation form submitted with too few beds should be invalid
        """
        self.default_data["num_beds"] = Listing.MIN_NUM_BEDS - 1
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("num_beds", tlf.errors.keys())

    def test_create_too_few_num_baths(self):
        """
        A creation form submitted with too few baths should be invalid
        :return:
        """
        self.default_data["num_baths"] = Listing.MIN_NUM_BATHS - 1
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("num_baths", tlf.errors.keys())

    def test_create_too_low_rent(self):
        """
        A creation form submitted with too low of a rent should be invalid
        :return:
        """
        self.default_data["rent_per_month"] = Listing.MIN_RENT - 1
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("rent_per_month", tlf.errors.keys())

    def test_create_missing_apt_name(self):
        """
        A creation form submitted without an apartment name should be invalid
        :return:
        """
        del self.default_data["apartment_name"]
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("apartment_name", tlf.errors.keys())

    def test_create_missing_apartment_description(self):
        """
        A creation form submitted without a apartment description should be invalid
        :return:
        """
        del self.default_data["apartment_description"]
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("apartment_description", tlf.errors.keys())

    def test_create_missing_listing_description(self):
        """
        A creation form submitted without a listing description should be invalid
        :return:
        """
        del self.default_data["listing_description"]
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("listing_description", tlf.errors.keys())

    def test_create_missing_address(self):
        """
        A creation form submitted without an address should be invalid
        :return:
        """
        del self.default_data["address"]
        tlf = CreateListingForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("address", tlf.errors.keys())

    def test_create_equivalence(self):
        """
        A creation form submitted with all required fields populated with valid data should be valid
        :return:
        """
        tlf = CreateListingForm(data=self.default_data)
        self.assertTrue(tlf.is_valid())

    
class AmenityFormTests(TestCase):
    def setUp(self) -> None: 
        self.default_data = {
            "amenity": "Pool" 
        }
    
    def test_empty_amenity(self):
        """
        Amenity form submitted empty
        """
        del self.default_data["amenity"]
        tlf = AmenityForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("amenity", tlf.errors.keys())

    def test_too_long_amenity(self):
        """
        Amenity form with too long input
        """
        self.default_data["amenity"] = "x" * 100
        tlf = AmenityForm(data=self.default_data)
        self.assertFalse(tlf.is_valid())
        self.assertIn("amenity", tlf.errors.keys())


class ReviewListingFormTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.default_data = DEFAULT_LISTING_CONSTANTS.copy()
        self.default_data["author"] = self.user
        self.listing = Listing(**self.default_data)
        self.listing.save()
        self.listing_name = self.listing.apartment_name

    def test_approved_side_effects(self):
        expected_message_text = f"Listing \"{self.listing_name}\" Approved - Feedback: approved!! and feedback"
        rlf = ReviewListingForm(
            instance=self.listing,
            data={
                "is_approved": True,
                "review_feedback": "approved!! and feedback"
            },
        )
        rlf.set_author(self.user)
        updated_listing = rlf.save()
        self.assertTrue(updated_listing.is_approved)
        self.assertTrue(updated_listing.is_reviewed)
        self.assertEqual(Message.objects.get(message=expected_message_text).message, expected_message_text)

    def test_denied_side_effects(self):
        expected_message_text = f"Listing \"{self.listing_name}\" Rejected - Feedback: denied!! and feedback"
        rlf = ReviewListingForm(instance=self.listing, data={
            "is_approved": False,
            "review_feedback": "denied!! and feedback"
        })
        rlf.set_author(self.user)
        updated_listing = rlf.save()
        self.assertFalse(updated_listing.is_approved)
        self.assertTrue(updated_listing.is_reviewed)
        self.assertEqual(Message.objects.get(message=expected_message_text).message, expected_message_text)


class UpdateListingFormTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.default_data = DEFAULT_LISTING_CONSTANTS.copy()
        self.default_data["author"] = self.user
        self.listing = Listing(**self.default_data)
        self.listing.save()

    def test_update_side_effects(self):
        # changing the number of beds should trigger a re-review
        self.default_data["num_beds"] = 30
        rlf = UpdateListingForm(
            instance=self.listing,
            data=self.default_data,
        )
        updated_listing = rlf.save()
        self.assertFalse(updated_listing.is_approved)
        self.assertFalse(updated_listing.is_reviewed)

    def test_update_hidden_field(self):
        # changing a field that is not supposed to trigger a re-review
        # should, unsurprisingly, not trigger a re-review

        # if there are no such fields, effectively skip this test
        if len(UpdateListingForm.no_review_fields) == 0:
            self.assertTrue(True)
            return

        # otherwise, check is_hidden specifically
        # (could make this test more robust another time, but not rly worth it)
        self.default_data["is_hidden"] = not self.default_data["is_hidden"]
        rlf = UpdateListingForm(
            instance=self.listing,
            data=self.default_data,
        )
        updated_listing = rlf.save()
        self.assertTrue(updated_listing.is_approved)
        self.assertTrue(updated_listing.is_reviewed)


class ListingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.default_data = DEFAULT_LISTING_CONSTANTS.copy()
        self.default_data["author"] = self.user

    def test_get_marker_js_with_address(self):
        """
        Test the get_marker_js method when the listing has an address.
        """
        listing = Listing(**self.default_data)
        with patch('requests.get') as mock_get:
            # Mock the requests.get function to return a successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "OK",
                "results": [{"geometry": {"location": {"lat": 123.45, "lng": 67.89}}}]
            }
            mock_get.return_value = mock_response

            marker_js = listing.get_marker_js()
            self.assertEqual(
                marker_js,
                'addMarker(123.45, 67.89, "test apt");'
            )

    def test_get_marker_js_without_address(self):
        """
        Test the get_marker_js method when the listing has no address.
        """
        listing = Listing(**self.default_data)
        listing.address = ""
        marker_js = listing.get_marker_js()
        self.assertEqual(marker_js, "")

    def test_get_info_window_js_with_address(self):
        """
        Test the get_info_window_js method when the listing has an address.
        """
        listing = Listing(**self.default_data)
        listing.save()
        listing_url = reverse('listing_detail', args=[listing.id])
        expected_info_content = (
            f"<h3>test apt</h3>"
            f"<p><b>Address:</b> raw address</p>"
            f"<p><b>Number of Beds:</b> 0 &nbsp;&nbsp;&nbsp; <b>Number of Baths:</b> 0</p>"
            f"<p><b>Rent per Month:</b> $0</p>"
            f"<p><a href='{listing_url}'>View Listing</a></p>"
        )
        expected_info_content = expected_info_content.replace("'", r"\'")
        info_window_js = listing.get_info_window_js()
        expected_js = f'addInfoWindow("{expected_info_content}");'
        self.assertEqual(info_window_js, expected_js)

class ListingFilterTests(TestCase):
    def setUp(self):
        self.default_data = {
            "apartment_name": "test apt",
            "parking": True,
            "num_beds": Listing.MIN_NUM_BEDS,
            "num_baths": Listing.MIN_NUM_BATHS,
            "rent_per_month": Listing.MIN_RENT,
        }
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        address1 = Address.objects.create(route="test address", street_number=1)
        address2 = Address.objects.create(route="test2 address", street_number=2)
        Listing.objects.create(
            author=self.user,
            address=address1,
            **self.default_data
        )
        Listing.objects.create(
            apartment_name="test2 apt",
            parking=False,
            num_beds=3,
            num_baths=3,
            rent_per_month=150000,
            address=address2,
            author=self.user
        )

    def test_filter_default_data(self):
        """
        Test to see if creating a filter with default values from above filters properly
        """
        listing_filter = ListingFilter(data=self.default_data)
        queryset = Listing.objects.all()
        filtered_queryset = listing_filter.qs
        expected_queryset = queryset.filter(
            apartment_name="test apt",
            parking=True,
            num_beds=Listing.MIN_NUM_BEDS,
            num_baths=Listing.MIN_NUM_BATHS,
            rent_per_month=Listing.MIN_RENT
        )
        self.assertQuerysetEqual(filtered_queryset, expected_queryset)

    def test_filter_address_street_number(self):
        """
        Test to see if address is filtered properly by street number (since Listings rely on a separate address model)
        """
        listing_filter = ListingFilter(data={"address": 1})
        queryset = Listing.objects.all()
        filtered_queryset = listing_filter.qs
        expected_queryset = queryset.filter(address__street_number__icontains='1')
        self.assertQuerysetEqual(filtered_queryset, expected_queryset)

    def test_filter_address_route(self):
        """
        Test to see if address is filtered properly by route (since Listings rely on a separate address model)
        """
        listing_filter = ListingFilter(data={"address": "test address"})
        queryset = Listing.objects.all()
        filtered_queryset = listing_filter.qs
        expected_queryset = queryset.filter(address__route__icontains='test address')
        self.assertQuerysetEqual(filtered_queryset, expected_queryset)

    def test_filter_no_parameters(self):
        """
        Test to see if empty filter returns all listings (count should be the same as unfiltered queryset)
        """
        listing_filter = ListingFilter(data={})
        filtered_queryset = listing_filter.qs
        all_listings = Listing.objects.all()
        self.assertEqual(all_listings.count(), filtered_queryset.count())

class ListingDetailViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(self.user)
        self.default_data = {
            "apartment_name": "test apt",
            "apartment_description": "desc",
            "listing_description": "desc",
            "listing_type": "Looking for Roommate",
            "lease_start": "2023-11-12",
            "lease_end": "2023-11-12",
            "address": "raw address",
            "place_id": "id",
            "parking": "True",
            "square_feet": Listing.MIN_SQUARE_FEET,
            "num_beds": Listing.MIN_NUM_BEDS,
            "num_baths": Listing.MIN_NUM_BATHS,
            "rent_per_month": Listing.MIN_RENT,
            "author": self.user,
            "utilities": None
            
        }
        self.listing = Listing(**self.default_data)
        self.listing.save()

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(reverse("listing_detail", args=(1, )))
        self.assertEqual(response.status_code, 302)

    def test_no_such_listing(self):
        """
        If the requested listing does not exist, appropriate response is shown
        """
        response = self.client.get(reverse("listing_detail", args=(99,)))
        self.assertEqual(response.status_code, 404)

    def test_listing_shows_name(self):
        resp = self.client.get(reverse("listing_detail", args=(1, )))
        self.assertContains(resp, self.default_data["apartment_name"])

    def test_listing_unprivileged_hidden_listing_view_permissions(self):
        """
        If the current user is not an admin and did not create a given listing,
        they cannot view a hidden listing
        """
        other_user = User.objects.create_user("user2", "pw2")
        self.client.force_login(other_user)
        self.listing.is_hidden = True
        self.listing.is_approved = True
        self.listing.save()
        resp = self.client.get(reverse("listing_detail", args=(1,)))
        self.assertEqual(resp.status_code, 403)

    def test_listing_unprivileged_unapproved_listing_view_permissions(self):
        """
        If the current user is not an admin and did not create a given listing,
        they cannot view a listing that is not approved
        """
        other_user = User.objects.create_user("user2", "pw2")
        self.client.force_login(other_user)
        self.listing.is_approved = False
        self.listing.save()
        resp = self.client.get(reverse("listing_detail", args=(1,)))
        self.assertEqual(resp.status_code, 403)


class CreateListingViewTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()

        response = self.client.get(reverse("create_listing"))
        self.assertEqual(response.status_code, 302)


class MessageTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.sender = User.objects.create_user(username='testsender', password='testpassword')
        self.client.force_login(self.user)

    def test_clear_messages(self):
        Message.objects.create(author=self.sender, recipient=self.user, message="hi")
        Message.objects.create(author=self.sender, recipient=self.user, message="hi")
        Message.objects.create(author=self.sender, recipient=self.user, message="hi")

        self.client.post(reverse("clear_messages"))

        self.assertTrue(Message.objects.filter(recipient=self.user).count() == 0)


