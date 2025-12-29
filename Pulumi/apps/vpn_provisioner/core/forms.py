from django import forms

class VPNForm(forms.Form):
    username = forms.CharField(required=True, max_length=20)
    code = forms.CharField(required=True, max_length=20)
    password = forms.CharField(required=True, widget=forms.PasswordInput)