from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Barber, Customer, Service, Equipment, Queue, PurchaseOrder
from .forms import BarberForm, CustomerForm, ServiceForm, EquipmentForm, PurchaseForm, QueueForm

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

# ===== PURCHASE =====
@login_required(login_url='/login/')
def purchase_list(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    purchases = PurchaseOrder.objects.all().order_by('-purchase_date')
    return render(request, 'purchase/purchase_list.html', {'purchases': purchases})

@login_required(login_url='/login/')
def purchase_add(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = request.user
            purchase.save()
            messages.success(request, f'บันทึกการซื้อ {purchase.equipment.name} จำนวน {purchase.quantity} เรียบร้อยแล้ว')
            return redirect('purchase_list')
    else:
        form = PurchaseForm(initial={'purchase_date': timezone.now().date()})
    return render(request, 'purchase/purchase_form.html', {'form': form})

@login_required(login_url='/login/')
def purchase_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    purchase = PurchaseOrder.objects.get(pk=pk)
    if request.method == 'POST':
        purchase.equipment.stock -= purchase.quantity
        if purchase.equipment.stock < 0:
            purchase.equipment.stock = 0
        purchase.equipment.save()
        purchase.delete()
        messages.success(request, 'ลบรายการซื้อเรียบร้อยแล้ว')
        return redirect('purchase_list')
    return render(request, 'purchase/purchase_confirm_delete.html', {'purchase': purchase})

# ===== QUEUE =====
@login_required(login_url='/login/')
def queue_list(request):
    if request.user.is_staff:
        queues = Queue.objects.all().order_by('-appointment_date', 'appointment_time')
    else:
        try:
            barber = Barber.objects.get(user=request.user)
            queues = Queue.objects.filter(barber=barber).order_by('-appointment_date', 'appointment_time')
        except Barber.DoesNotExist:
            queues = []
    return render(request, 'queue/queue_list.html', {'queues': queues})

@login_required(login_url='/login/')
def queue_add(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    if request.method == 'POST':
        form = QueueForm(request.POST)
        if form.is_valid():
            barber = form.cleaned_data['barber']
            appointment_date = form.cleaned_data['appointment_date']
            appointment_time = form.cleaned_data['appointment_time']

            # เช็คว่าช่างว่างมั้ยในช่วงเวลานั้น
            existing = Queue.objects.filter(
                barber=barber,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['waiting', 'in_progress']
            ).exists()

            if existing:
                messages.error(request, f'ช่าง {barber.name} ไม่ว่างในเวลานี้ กรุณาเลือกเวลาอื่น')
            else:
                form.save()
                messages.success(request, 'เพิ่มคิวเรียบร้อยแล้ว')
                return redirect('queue_list')
    else:
        form = QueueForm(initial={'appointment_date': timezone.now().date()})
    return render(request, 'queue/queue_form.html', {'form': form, 'action': 'เพิ่ม'})

@login_required(login_url='/login/')
def queue_edit(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    queue = Queue.objects.get(pk=pk)
    if request.method == 'POST':
        form = QueueForm(request.POST, instance=queue)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขคิวเรียบร้อยแล้ว')
            return redirect('queue_list')
    else:
        form = QueueForm(instance=queue)
    return render(request, 'queue/queue_form.html', {'form': form, 'action': 'แก้ไข', 'queue': queue})

@login_required(login_url='/login/')
def queue_update_status(request, pk):
    queue = Queue.objects.get(pk=pk)
    if request.user.is_staff or (hasattr(request.user, 'barber') and queue.barber.user == request.user):
        if request.method == 'POST':
            status = request.POST.get('status')
            queue.status = status
            queue.save()
            messages.success(request, 'อัปเดตสถานะคิวเรียบร้อยแล้ว')
    return redirect('queue_list')

@login_required(login_url='/login/')
def queue_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    queue = Queue.objects.get(pk=pk)
    if request.method == 'POST':
        queue.delete()
        messages.success(request, 'ลบคิวเรียบร้อยแล้ว')
        return redirect('queue_list')
    return render(request, 'queue/queue_confirm_delete.html', {'queue': queue})
from .models import Barber, Customer, Service, Equipment, Queue, PurchaseOrder, ServiceRecord, ServiceRecordItem
from .forms import BarberForm, CustomerForm, ServiceForm, EquipmentForm, PurchaseForm, QueueForm, ServiceRecordForm

# ===== SERVICE RECORD =====
@login_required(login_url='/login/')
def service_record_list(request):
    if request.user.is_staff:
        records = ServiceRecord.objects.all().order_by('-service_date')
    else:
        try:
            barber = Barber.objects.get(user=request.user)
            records = ServiceRecord.objects.filter(barber=barber).order_by('-service_date')
        except Barber.DoesNotExist:
            records = []
    return render(request, 'service_record/service_record_list.html', {'records': records})

@login_required(login_url='/login/')
def service_record_add(request):
    if request.method == 'POST':
        form = ServiceRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            # คำนวณราคารวม
            service_ids = request.POST.getlist('service_id')
            quantities = request.POST.getlist('quantity')
            total = 0
            for sid, qty in zip(service_ids, quantities):
                try:
                    service = Service.objects.get(pk=sid)
                    total += service.price * int(qty)
                except:
                    pass
            record.total_price = total
            record.save()
            # บันทึกรายการบริการ
            for sid, qty in zip(service_ids, quantities):
                try:
                    service = Service.objects.get(pk=sid)
                    ServiceRecordItem.objects.create(
                        record=record,
                        service=service,
                        quantity=int(qty),
                        price=service.price
                    )
                except:
                    pass
            messages.success(request, 'บันทึกการใช้บริการเรียบร้อยแล้ว')
            return redirect('service_record_list')
    else:
        form = ServiceRecordForm(initial={'service_date': timezone.now().date()})
        if not request.user.is_staff:
            try:
                barber = Barber.objects.get(user=request.user)
                form.fields['barber'].initial = barber
            except:
                pass
    services = Service.objects.filter(is_active=True)
    return render(request, 'service_record/service_record_form.html', {
        'form': form,
        'services': services
    })

@login_required(login_url='/login/')
def service_record_detail(request, pk):
    record = ServiceRecord.objects.get(pk=pk)
    if not request.user.is_staff:
        try:
            barber = Barber.objects.get(user=request.user)
            if record.barber != barber:
                return redirect('service_record_list')
        except:
            return redirect('service_record_list')
    items = record.items.all()
    return render(request, 'service_record/service_record_detail.html', {
        'record': record,
        'items': items
    })

@login_required(login_url='/login/')
def service_record_pay(request, pk):
    record = ServiceRecord.objects.get(pk=pk)
    if request.method == 'POST':
        record.is_paid = True
        record.save()
        messages.success(request, 'บันทึกการชำระเงินเรียบร้อยแล้ว')
    return redirect('service_record_list')

@login_required(login_url='/login/')
def service_record_delete(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    record = ServiceRecord.objects.get(pk=pk)
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'ลบรายการเรียบร้อยแล้ว')
        return redirect('service_record_list')
    return render(request, 'service_record/service_record_confirm_delete.html', {'record': record})