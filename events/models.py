"""
DATABASE SCHEMA
===============
Event          — admin creates events (name, date, venue, fee, type)
StudentProfile — extends Django User with college + phone
Registration   — one row per student-event pair
                 tracks: participation type, group info,
                         payment screenshot, payment status,
                         unique_code (generated after verification)
"""

from django.db import models
from django.contrib.auth.models import User
import random, string


# ── Student profile (extends built-in User) ──────────────────────
class StudentProfile(models.Model):
    user    = models.OneToOneField(User, on_delete=models.CASCADE,
                                   related_name='profile')
    college = models.CharField(max_length=200)
    phone   = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.college})"


# ── Event ─────────────────────────────────────────────────────────
class Event(models.Model):
    CATEGORY = [
        ('technical', 'Technical'),
        ('cultural',  'Cultural'),
        ('sports',    'Sports'),
        ('other',     'Other'),
    ]
    ETYPE = [
        ('solo',  'Solo Only'),
        ('group', 'Group Only'),
        ('both',  'Solo & Group'),
    ]

    name             = models.CharField(max_length=200)
    description      = models.TextField(blank=True)
    date             = models.DateField()
    venue            = models.CharField(max_length=200)
    category         = models.CharField(max_length=20, choices=CATEGORY, default='technical')
    event_type       = models.CharField(max_length=10, choices=ETYPE, default='both')
    registration_fee = models.DecimalField(max_digits=8, decimal_places=2)
    max_participants = models.PositiveIntegerField(default=100)
    upi_id           = models.CharField(max_length=100, default='college@upi',
                                        help_text='UPI ID students should pay to')
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL,
                                         null=True, related_name='created_events')
    created_at       = models.DateTimeField(auto_now_add=True)
    is_active        = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.name

    @property
    def confirmed_count(self):
        return self.registrations.filter(payment_status='verified').count()

    @property
    def slots_left(self):
        return max(0, self.max_participants - self.confirmed_count)


# ── Registration ──────────────────────────────────────────────────
class Registration(models.Model):
    PTYPE = [
        ('solo',  'Solo'),
        ('group', 'Group'),
    ]
    PAY_STATUS = [
        ('not_uploaded', 'Not Uploaded'),
        ('pending',      'Pending Verification'),
        ('verified',     'Verified'),
        ('rejected',     'Rejected'),
    ]

    # Core relationship
    student = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='registrations')
    event   = models.ForeignKey(Event, on_delete=models.CASCADE,
                                related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    # Participation
    participation_type = models.CharField(max_length=10, choices=PTYPE, default='solo')
    group_name         = models.CharField(max_length=200, blank=True)
    member_names       = models.TextField(blank=True,
                            help_text='Comma-separated member names (for group)')

    # Payment
    payment_screenshot  = models.ImageField(upload_to='payments/%Y/%m/',
                                            blank=True, null=True)
    payment_status      = models.CharField(max_length=20, choices=PAY_STATUS,
                                           default='not_uploaded')
    payment_uploaded_at = models.DateTimeField(null=True, blank=True)

    # Admin action
    verified_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='verified_registrations')
    verified_at      = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Generated after verification
    unique_code = models.CharField(max_length=20, blank=True, unique=True, null=True)

    class Meta:
        ordering = ['-registered_at']
        unique_together = [['student', 'event']]   # one registration per student per event

    def __str__(self):
        return f"{self.student.get_full_name()} → {self.event.name}"

    # ── helpers ──────────────────────────────────────────────────
    def generate_unique_code(self):
        """TQ-8472 style code — event prefix + 4 random digits"""
        prefix = ''.join(c for c in self.event.name[:3] if c.isalpha()).upper()
        while True:
            code = f"{prefix}-{''.join(random.choices(string.digits, k=4))}"
            if not Registration.objects.filter(unique_code=code).exists():
                return code

    def get_member_list(self):
        if self.member_names:
            return [m.strip() for m in self.member_names.split(',') if m.strip()]
        return []

    @property
    def status_label(self):
        labels = {
            'not_uploaded': ('gray',  'Awaiting Payment'),
            'pending':      ('amber', 'Under Review'),
            'verified':     ('green', 'Confirmed'),
            'rejected':     ('red',   'Rejected'),
        }
        return labels.get(self.payment_status, ('gray', self.payment_status))
