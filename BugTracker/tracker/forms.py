from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import UserProfile, Bug, Comment, ROLE_CHOICES, ROLE_DEVELOPER

class RegistrationForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, required=True, 
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Full Name'}))
    username = forms.CharField(max_length=150, required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create password'}),
                               min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial=ROLE_DEVELOPER,
                             widget=forms.Select(attrs={'class': 'form-select'}))
    photo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username').lower()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=254, required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))


class BugForm(forms.ModelForm):
    class Meta:
        model = Bug
        fields = ['title', 'description', 'project_name', 'module_name', 'bug_type', 'priority', 'severity']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bug title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the bug, steps to reproduce, and expected vs actual results...'}),
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Name'}),
            'module_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Module Name (e.g. Auth, Payment, Frontend)'}),
            'bug_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment_text']
        widgets = {
            'comment_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write a comment or reply...'}),
        }


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    photo = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['photo']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        user = self.instance.user
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise ValidationError("A user with this email address already exists.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile
