import django_filters
from .models import Listing
from django.db.models import Q

class ListingFilter(django_filters.FilterSet):
    #possible fields to filter by
    apartment_name = django_filters.CharFilter(lookup_expr='icontains', label='Apartment Name')
    address = django_filters.CharFilter(method='filter_address', label='Address')
    parking = django_filters.BooleanFilter(label='Parking')
    num_beds = django_filters.NumberFilter(field_name='num_beds', label='Number of Beds', lookup_expr='exact')
    num_baths = django_filters.NumberFilter(field_name='num_baths', label='Number of Bathrooms', lookup_expr='exact')
    rent_per_month = django_filters.NumberFilter(label='Rent per Month', lookup_expr='lte')

    class Meta:
        model = Listing
        #list of fields that the filter can filter by
        fields = [
            'apartment_name',
            'parking',
            'num_beds',
            'num_baths',
            'rent_per_month',
        ]

    def filter_address(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(address__street_number__icontains=value) | Q(address__route__icontains=value)
            )
        return queryset