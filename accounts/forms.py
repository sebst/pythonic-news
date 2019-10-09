from django import forms

from .models import CustomUser, Invitation

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['about', 'email']
    
    def clean_email(self):
        data = self.cleaned_data['email']
        if data:
            data = data.lower()
        return data


class RegisterForm(forms.ModelForm):
    MIN_LENGTH = 8
    class Meta:
        model = CustomUser
        fields = ['username', 'password', 'email']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < self.MIN_LENGTH:
            raise forms.ValidationError("Your password must be at least %d characters long." % self.MIN_LENGTH)
        return password

class CreateInviteForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['invited_email_address']
    
    def clean_invited_email_address(self):
        invited_email_address = self.cleaned_data['invited_email_address']
        if invited_email_address:
            invited_email_address = invited_email_address.lower()
        return invited_email_address


class PasswordForgottenForm(forms.Form):
    username = forms.CharField()

class PasswortResetForm(forms.Form):
    password = forms.CharField()