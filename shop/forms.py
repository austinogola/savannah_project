# forms.py
from django import forms
from .models import Customer

# Example country codes, you can expand as needed
COUNTRY_CODES = [
    ('+1', 'US (+1)'),
    ('+44', 'UK (+44)'),
    ('+254', 'Kenya (+254)'),
    ('+91', 'India (+91)'),
    # Add more codes here
]

class CustomerPhoneForm(forms.ModelForm):
    country_code = forms.ChoiceField(choices=COUNTRY_CODES, initial='+254')
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'placeholder': 'Enter phone number'}))

    class Meta:
        model = Customer
        fields = ['country_code', 'phone']
    
    def save(self, commit=True):
        # Combine country code + phone into the model's phone field
        customer = super().save(commit=False)
        customer.phone = f"{self.cleaned_data['country_code']}{self.cleaned_data['phone']}"
        if commit:
            customer.save()
        return customer
