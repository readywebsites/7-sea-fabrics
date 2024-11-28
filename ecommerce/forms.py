import json
from django import forms
from django.contrib.auth.models import User
from ecommerce.models import UserProfile, Order, Address


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['first_name', 'last_name', 'email', 'phone', 'address_line_1', 'country', 'state', 'city', 'zipcode']

    def __init__(self, user, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['existing_address'] = forms.ModelChoiceField(
            queryset=Address.objects.filter(user=user),
            empty_label="(Choose an existing address)",
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'additional_addresses']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['additional_addresses'].widget = forms.Textarea(attrs={'rows': 3})

    def clean_additional_addresses(self):
        data = self.cleaned_data['additional_addresses']
        try:
            addresses = json.loads(data)
            if not isinstance(addresses, list):
                raise forms.ValidationError("Invalid data format. Should be a list of addresses.")
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format.")
        return data
    
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = []  # Remove 'products' from here

    def __init__(self, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)