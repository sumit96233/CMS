from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Event, Registration, StudentProfile


# ── Student sign-up ───────────────────────────────────────────────
class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name  = forms.CharField(max_length=100)
    email      = forms.EmailField()
    college    = forms.CharField(max_length=200)
    phone      = forms.CharField(max_length=15)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'college', 'phone',
                  'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        if commit:
            user.save()
            StudentProfile.objects.create(
                user    = user,
                college = self.cleaned_data['college'],
                phone   = self.cleaned_data['phone'],
            )
        return user


# ── Admin: create/edit event ──────────────────────────────────────
class EventForm(forms.ModelForm):
    class Meta:
        model  = Event
        fields = ['name', 'description', 'date', 'venue', 'category',
                  'event_type', 'registration_fee', 'max_participants',
                  'upi_id', 'is_active']
        widgets = {
            'date':        forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ── Student: register for an event ───────────────────────────────
class RegistrationForm(forms.ModelForm):
    class Meta:
        model  = Registration
        fields = ['participation_type', 'group_name', 'member_names']
        widgets = {
            'member_names': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g.  Rahul Sharma, Priya Nair, Aman Verma'
            }),
        }

    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        # Restrict options based on event type
        if event.event_type == 'solo':
            self.fields['participation_type'].choices = [('solo', 'Solo')]
        elif event.event_type == 'group':
            self.fields['participation_type'].choices = [('group', 'Group')]

    def clean(self):
        data  = super().clean()
        ptype = data.get('participation_type')
        if ptype == 'group':
            if not data.get('group_name'):
                self.add_error('group_name', 'Team name is required for group participation.')
            if not data.get('member_names'):
                self.add_error('member_names', 'List all member names.')
        return data


# ── Student: upload payment screenshot ───────────────────────────
class PaymentForm(forms.ModelForm):
    class Meta:
        model   = Registration
        fields  = ['payment_screenshot']
        widgets = {'payment_screenshot': forms.FileInput(attrs={'accept': 'image/*'})}


# ── Admin: verify or reject a payment ────────────────────────────
class VerifyForm(forms.Form):
    DECISION = [('verified', '✓  Verify — payment is correct'),
                ('rejected', '✗  Reject — payment has a problem')]
    decision         = forms.ChoiceField(choices=DECISION, widget=forms.RadioSelect)
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2,
            'placeholder': 'Required when rejecting — explain why'}),
    )

    def clean(self):
        data = super().clean()
        if data.get('decision') == 'rejected' and not data.get('rejection_reason', '').strip():
            self.add_error('rejection_reason', 'Please give a reason for rejection.')
        return data
