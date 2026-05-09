from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Barber, Customer, Service, Equipment, Queue, PurchaseOrder

# ===== LOGIN =====
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            from django.contrib.auth.forms import AuthenticationForm
            form = AuthenticationForm()
            form.errors['__all__'] = ['ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง']
            return render(request, 'login.html', {'form': form})
    from django.contrib.auth.forms import AuthenticationForm
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# ===== LOGOUT =====
def logout_view(request):
    logout(request)
    return redirect('login')

# ===== DASHBOARD =====
@login_required(login_url='/login/')
def dashboard(request):
    today = timezone.now().date()

    if request.user.is_staff:
        today_queues = Queue.objects.filter(appointment_date=today).count()
        queues = Queue.objects.filter(appointment_date=today).order_by('appointment_time')
        context = {
            'total_barbers': Barber.objects.filter(is_active=True).count(),
            'total_customers': Customer.objects.count(),
            'today_queues': today_queues,
            'today_income': 0,
            'queues': queues,
        }
    else:
        try:
            barber = Barber.objects.get(user=request.user)
            queues = Queue.objects.filter(barber=barber, appointment_date=today).order_by('appointment_time')
            context = {
                'today_queues': queues.filter(status='waiting').count(),
                'done_queues': queues.filter(status='done').count(),
                'queues': queues,
            }
        except Barber.DoesNotExist:
            context = {
                'today_queues': 0,
                'done_queues': 0,
                'queues': [],
            }

    return render(request, 'dashboard.html', context)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import BarberForm, CustomerForm, ServiceForm, EquipmentForm

# ===== BARBER =====
@login_required(login_url='/login/')
def barber_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    barbers = Barber.objects.all()
    return render(request, 'barber/barber_list.html', {'barbers': barbers})

@login_required(login_url='/login/')
def barber_add(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = BarberForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if User.objects.filter(username=username).exists():
                messages.error(request, 'ชื่อผู้ใช้นี้มีอยู่แล้ว')
            else:
                user = User.objects.create_user(username=username, password=password)
                barber = form.save(commit=False)
                barber.user = user
                barber.save()
                messages.success(request, 'เพิ่มข้อมูลช่างเรียบร้อยแล้ว')
                return redirect('barber_list')
    else:
        form = BarberForm()
    return render(request, 'barber/barber_form.html', {'form': form, 'action': 'เพิ่ม'})

@login_required(login_url='/login/')
def barber_edit(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    barber = Barber.objects.get(pk=pk)
    if request.method == 'POST':
        form = BarberForm(request.POST, request.FILES, instance=barber, instance_user=barber.user)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = barber.user
            if user:
                if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                    messages.error(request, 'ชื่อผู้ใช้นี้มีอยู่แล้ว')
                    return render(request, 'barber/barber_form.html', {'form': form, 'action': 'แก้ไข'})
                user.username = username
                if password:
                    user.set_password(password)
                user.save()
            barber = form.save()
            messages.success(request, 'แก้ไขข้อมูลช่างเรียบร้อยแล้ว')
            return redirect('barber_list')
    else:
        form = BarberForm(instance=barber, instance_user=barber.user)
    return render(request, 'barber/barber_form.html', {'form': form, 'action': 'แก้ไข', 'barber': barber})

@login_required(login_url='/login/')
def barber_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    barber = Barber.objects.get(pk=pk)
    if request.method == 'POST':
        if barber.user:
            barber.user.delete()
        barber.delete()
        messages.success(request, 'ลบข้อมูลช่างเรียบร้อยแล้ว')
        return redirect('barber_list')
    return render(request, 'barber/barber_confirm_delete.html', {'barber': barber})

# ===== CUSTOMER =====
@login_required(login_url='/login/')
def customer_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    customers = Customer.objects.all().order_by('-created_at')
    return render(request, 'customer/customer_list.html', {'customers': customers})

@login_required(login_url='/login/')
def customer_add(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มข้อมูลลูกค้าเรียบร้อยแล้ว')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'customer/customer_form.html', {'form': form, 'action': 'เพิ่ม'})

@login_required(login_url='/login/')
def customer_edit(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    customer = Customer.objects.get(pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลลูกค้าเรียบร้อยแล้ว')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'customer/customer_form.html', {'form': form, 'action': 'แก้ไข'})

@login_required(login_url='/login/')
def customer_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    customer = Customer.objects.get(pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'ลบข้อมูลลูกค้าเรียบร้อยแล้ว')
        return redirect('customer_list')
    return render(request, 'customer/customer_confirm_delete.html', {'customer': customer})

# ===== SERVICE =====
@login_required(login_url='/login/')
def service_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    services = Service.objects.all()
    return render(request, 'service/service_list.html', {'services': services})

@login_required(login_url='/login/')
def service_add(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มบริการเรียบร้อยแล้ว')
            return redirect('service_list')
    else:
        form = ServiceForm()
    return render(request, 'service/service_form.html', {'form': form, 'action': 'เพิ่ม'})

@login_required(login_url='/login/')
def service_edit(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    service = Service.objects.get(pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขบริการเรียบร้อยแล้ว')
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'service/service_form.html', {'form': form, 'action': 'แก้ไข'})

@login_required(login_url='/login/')
def service_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    service = Service.objects.get(pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'ลบบริการเรียบร้อยแล้ว')
        return redirect('service_list')
    return render(request, 'service/service_confirm_delete.html', {'service': service})

# ===== EQUIPMENT =====
@login_required(login_url='/login/')
def equipment_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    equipments = Equipment.objects.all()
    return render(request, 'equipment/equipment_list.html', {'equipments': equipments})

@login_required(login_url='/login/')
def equipment_add(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มอุปกรณ์เรียบร้อยแล้ว')
            return redirect('equipment_list')
    else:
        form = EquipmentForm()
    return render(request, 'equipment/equipment_form.html', {'form': form, 'action': 'เพิ่ม'})

@login_required(login_url='/login/')
def equipment_edit(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    equipment = Equipment.objects.get(pk=pk)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขอุปกรณ์เรียบร้อยแล้ว')
            return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'equipment/equipment_form.html', {'form': form, 'action': 'แก้ไข'})

@login_required(login_url='/login/')
def equipment_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    equipment = Equipment.objects.get(pk=pk)
    if request.method == 'POST':
        equipment.delete()
        messages.success(request, 'ลบอุปกรณ์เรียบร้อยแล้ว')
        return redirect('equipment_list')
    return render(request, 'equipment/equipment_confirm_delete.html', {'equipment': equipment})