from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count

from .models  import Event, Registration, StudentProfile
from .forms   import SignupForm, EventForm, RegistrationForm, PaymentForm, VerifyForm


# ── permission helper ─────────────────────────────────────────────
def admin_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))


# ═════════════════════════════════════════════════════════════════
#  AUTH
# ═════════════════════════════════════════════════════════════════
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('admin_dashboard' if request.user.is_staff else 'event_list')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome {user.first_name}! Browse events below.")
        return redirect('event_list')
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('admin_dashboard' if user.is_staff else 'event_list')
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ═════════════════════════════════════════════════════════════════
#  STUDENT — browse & register
# ═════════════════════════════════════════════════════════════════
@login_required
def event_list(request):
    events = Event.objects.filter(is_active=True)

    q        = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    if q:
        events = events.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category:
        events = events.filter(category=category)

    my_ids = set(Registration.objects.filter(
        student=request.user).values_list('event_id', flat=True)
    )
    return render(request, 'events/event_list.html', {
        'events':      events,
        'my_ids':      my_ids,
        'q':           q,
        'category':    category,
        'categories':  Event.CATEGORY,
    })


@login_required
def register_event(request, pk):
    event = get_object_or_404(Event, pk=pk, is_active=True)

    if Registration.objects.filter(student=request.user, event=event).exists():
        messages.info(request, "You already registered for this event.")
        return redirect('my_registrations')

    if event.slots_left == 0:
        messages.error(request, "This event is full.")
        return redirect('event_list')

    form = RegistrationForm(event, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reg = form.save(commit=False)
        reg.student = request.user
        reg.event   = event
        if reg.participation_type == 'solo':
            reg.group_name   = ''
            reg.member_names = ''
        reg.save()
        messages.success(request, "Registered! Now upload your payment screenshot.")
        return redirect('upload_payment', pk=reg.pk)

    return render(request, 'events/register_form.html', {'event': event, 'form': form})


@login_required
def upload_payment(request, pk):
    reg = get_object_or_404(Registration, pk=pk, student=request.user)

    if reg.payment_status == 'verified':
        messages.info(request, "Payment already verified.")
        return redirect('my_registrations')

    form = PaymentForm(request.POST or None, request.FILES or None, instance=reg)
    if request.method == 'POST' and form.is_valid():
        r = form.save(commit=False)
        r.payment_status      = 'pending'
        r.payment_uploaded_at = timezone.now()
        r.save()
        messages.success(request, "Screenshot uploaded. Admin will verify shortly.")
        return redirect('my_registrations')

    return render(request, 'events/upload_payment.html', {'reg': reg, 'form': form})


@login_required
def my_registrations(request):
    regs = Registration.objects.filter(
        student=request.user
    ).select_related('event').order_by('-registered_at')
    return render(request, 'events/my_registrations.html', {'regs': regs})


# ═════════════════════════════════════════════════════════════════
#  ADMIN — dashboard, events, registrations, verify
# ═════════════════════════════════════════════════════════════════
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    ctx = {
        'total_events':        Event.objects.count(),
        'active_events':       Event.objects.filter(is_active=True).count(),
        'total_regs':          Registration.objects.count(),
        'pending_count':       Registration.objects.filter(payment_status='pending').count(),
        'verified_count':      Registration.objects.filter(payment_status='verified').count(),
        'recent_regs':         Registration.objects.select_related(
                                   'student', 'event'
                               ).order_by('-registered_at')[:6],
        'pending_regs':        Registration.objects.filter(
                                   payment_status='pending'
                               ).select_related('student', 'event')[:5],
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


# ── Events CRUD ───────────────────────────────────────────────────
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_events(request):
    events = Event.objects.annotate(
        reg_count=Count('registrations')
    ).order_by('-created_at')
    return render(request, 'admin_panel/events.html', {'events': events})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_event_create(request):
    form = EventForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ev = form.save(commit=False)
        ev.created_by = request.user
        ev.save()
        messages.success(request, f"Event '{ev.name}' created.")
        return redirect('admin_events')
    return render(request, 'admin_panel/event_form.html',
                  {'form': form, 'title': 'Create New Event'})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_event_edit(request, pk):
    ev   = get_object_or_404(Event, pk=pk)
    form = EventForm(request.POST or None, instance=ev)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Event updated.")
        return redirect('admin_events')
    return render(request, 'admin_panel/event_form.html',
                  {'form': form, 'title': f'Edit — {ev.name}', 'event': ev})


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_event_toggle(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    ev.is_active = not ev.is_active
    ev.save()
    messages.success(request, f"Event {'activated' if ev.is_active else 'deactivated'}.")
    return redirect('admin_events')


# ── Registrations list ────────────────────────────────────────────
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_registrations(request):
    qs = Registration.objects.select_related(
        'student', 'event', 'student__profile'
    ).order_by('-registered_at')

    # filters
    event_id = request.GET.get('event', '')
    status   = request.GET.get('status', '')
    q        = request.GET.get('q', '').strip()

    if event_id:
        qs = qs.filter(event_id=event_id)
    if status:
        qs = qs.filter(payment_status=status)
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) |
            Q(student__last_name__icontains=q)  |
            Q(student__email__icontains=q)       |
            Q(unique_code__icontains=q)
        )

    return render(request, 'admin_panel/registrations.html', {
        'regs':          qs,
        'events':        Event.objects.all(),
        'sel_event':     event_id,
        'sel_status':    status,
        'q':             q,
        'pending_count': Registration.objects.filter(payment_status='pending').count(),
        'status_opts':   Registration.PAY_STATUS,
    })


# ── Verify payment ────────────────────────────────────────────────
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_verify(request, pk):
    reg  = get_object_or_404(
        Registration.objects.select_related('student', 'event', 'student__profile'), pk=pk
    )
    form = VerifyForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        decision = form.cleaned_data['decision']
        reg.payment_status = decision
        reg.verified_by    = request.user
        reg.verified_at    = timezone.now()

        if decision == 'verified':
            reg.unique_code = reg.generate_unique_code()
            messages.success(request,
                f"✅ Payment verified. QR code {reg.unique_code} assigned to "
                f"{reg.student.get_full_name()}.")
        else:
            reg.rejection_reason = form.cleaned_data['rejection_reason']
            messages.warning(request,
                f"❌ Payment rejected for {reg.student.get_full_name()}.")

        reg.save()
        return redirect('admin_registrations')

    return render(request, 'admin_panel/verify.html', {'reg': reg, 'form': form})
