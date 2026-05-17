import csv
from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import F, Count, Sum
from .models import Barber, Customer, Service, Equipment, Queue, PurchaseOrder, ServiceRecord, ServiceRecordItem
from .forms import BarberForm, CustomerForm, ServiceForm, EquipmentForm, PurchaseForm, QueueForm, ServiceRecordForm

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
        
        # Calculate today's real income
        today_records = ServiceRecord.objects.filter(service_date=today, is_paid=True)
        today_income_val = sum(record.total_price for record in today_records)
        
        # Low stock equipment (exclude items where min_stock is 0, which means disabled warning)
        low_stock = Equipment.objects.filter(stock__lte=F('min_stock')).exclude(min_stock=0)[:5]
        
        # Recent service records
        recent_records = ServiceRecord.objects.order_by('-created_at')[:5]
        
        context = {
            'total_barbers': Barber.objects.filter(is_active=True).count(),
            'total_customers': Customer.objects.count(),
            'today_queues': today_queues,
            'today_income': today_income_val,
            'queues': queues,
            'low_stock': low_stock,
            'recent_records': recent_records,
        }
    else:
        try:
            barber = Barber.objects.get(user=request.user)
            queues = Queue.objects.filter(barber=barber, appointment_date=today).order_by('appointment_time')
            recent_records = ServiceRecord.objects.filter(barber=barber).order_by('-created_at')[:5]
            
            barber_records_today = ServiceRecord.objects.filter(barber=barber, service_date=today, is_paid=True)
            my_income = sum(record.total_price for record in barber_records_today)
            
            context = {
                'today_queues': queues.count(),
                'waiting_queues': queues.filter(status='waiting').count(),
                'done_queues': queues.filter(status='done').count(),
                'my_income': my_income,
                'queues': queues,
                'recent_records': recent_records,
            }
        except Barber.DoesNotExist:
            context = {
                'today_queues': 0,
                'waiting_queues': 0,
                'done_queues': 0,
                'my_income': 0,
                'queues': [],
                'recent_records': [],
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
            equipment_name = form.cleaned_data['equipment_name']
            equipment = Equipment.objects.filter(name=equipment_name).first()
            if not equipment:
                equipment = Equipment.objects.create(name=equipment_name, unit='ชิ้น', min_stock=5)

            purchase = form.save(commit=False)
            purchase.equipment = equipment
            purchase.created_by = request.user
            purchase.save()
            messages.success(request, f'บันทึกการซื้อ {purchase.equipment.name} จำนวน {purchase.quantity} เรียบร้อยแล้ว')
            return redirect('purchase_list')
    else:
        form = PurchaseForm(initial={'purchase_date': timezone.now().date()})
        
    equipments = Equipment.objects.all()
    return render(request, 'purchase/purchase_form.html', {'form': form, 'action': 'เพิ่ม', 'equipments': equipments})

@login_required(login_url='/login/')
def purchase_edit(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
    purchase = PurchaseOrder.objects.get(pk=pk)
    old_quantity = purchase.quantity
    old_equipment = purchase.equipment
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            equipment_name = form.cleaned_data['equipment_name']
            equipment = Equipment.objects.filter(name=equipment_name).first()
            if not equipment:
                equipment = Equipment.objects.create(name=equipment_name, unit='ชิ้น', min_stock=5)

            new_purchase = form.save(commit=False)
            new_purchase.equipment = equipment
            
            if new_purchase.equipment == old_equipment:
                diff = new_purchase.quantity - old_quantity
                new_purchase.equipment.stock += diff
                new_purchase.equipment.save()
            else:
                old_equipment.stock -= old_quantity
                old_equipment.save()
                # We do not use new_purchase.equipment.stock += new_purchase.quantity 
                # directly here without reloading because if it's newly created, stock is 0.
                # Actually wait, model save() method adds quantity to stock for new pk, 
                # but for update it doesn't? Let's check PurchaseOrder.save()
                # Since we manually handle it here, we add to the new equipment's stock:
                new_purchase.equipment.stock += new_purchase.quantity
                new_purchase.equipment.save()
                
            new_purchase.save()
            messages.success(request, 'แก้ไขการซื้อเรียบร้อยแล้ว')
            return redirect('purchase_list')
    else:
        initial_data = {}
        if purchase.equipment:
            initial_data['equipment_name'] = purchase.equipment.name
        form = PurchaseForm(instance=purchase, initial=initial_data)
        
    equipments = Equipment.objects.all()
    return render(request, 'purchase/purchase_form.html', {'form': form, 'action': 'แก้ไข', 'equipments': equipments})

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
        try:
            barber_obj = Barber.objects.get(user=request.user)
        except Barber.DoesNotExist:
            return redirect('dashboard')
    else:
        barber_obj = None

    if request.method == 'POST':
        form = QueueForm(request.POST)
        if form.is_valid():
            customer_name = form.cleaned_data['customer_name']
            barber = barber_obj if barber_obj else form.cleaned_data['barber']
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
                # Find or create customer
                customer = Customer.objects.filter(name=customer_name).first()
                if not customer:
                    customer = Customer.objects.create(name=customer_name, phone='0000000000')
                
                queue = form.save(commit=False)
                queue.customer = customer
                queue.barber = barber
                queue.save()
                messages.success(request, 'เพิ่มคิวเรียบร้อยแล้ว')
                return redirect('queue_list')
    else:
        form = QueueForm(initial={'appointment_date': timezone.now().date()})
        if barber_obj:
            form.fields['barber'].initial = barber_obj
            form.fields['barber'].widget = forms.HiddenInput()
    
    customers = Customer.objects.all()
    return render(request, 'queue/queue_form.html', {'form': form, 'action': 'เพิ่ม', 'customers': customers})

@login_required(login_url='/login/')
def queue_edit(request, pk):
    queue = Queue.objects.get(pk=pk)
    if not request.user.is_staff:
        try:
            barber_obj = Barber.objects.get(user=request.user)
            if queue.barber != barber_obj:
                return redirect('dashboard')
        except Barber.DoesNotExist:
            return redirect('dashboard')
    else:
        barber_obj = None

    if request.method == 'POST':
        form = QueueForm(request.POST, instance=queue)
        if form.is_valid():
            customer_name = form.cleaned_data['customer_name']
            customer = Customer.objects.filter(name=customer_name).first()
            if not customer:
                customer = Customer.objects.create(name=customer_name, phone='0000000000')
            
            queue = form.save(commit=False)
            queue.customer = customer
            if barber_obj:
                queue.barber = barber_obj
            queue.save()
            messages.success(request, 'แก้ไขคิวเรียบร้อยแล้ว')
            return redirect('queue_list')
    else:
        initial_data = {}
        if queue.customer:
            initial_data['customer_name'] = queue.customer.name
        form = QueueForm(instance=queue, initial=initial_data)
        if barber_obj:
            form.fields['barber'].widget = forms.HiddenInput()
        
    customers = Customer.objects.all()
    return render(request, 'queue/queue_form.html', {'form': form, 'action': 'แก้ไข', 'queue': queue, 'customers': customers})

@login_required(login_url='/login/')
def queue_update_status(request, pk):
    queue = Queue.objects.get(pk=pk)
    if request.user.is_staff or (hasattr(request.user, 'barber') and queue.barber.user == request.user):
        if request.method == 'POST':
            status = request.POST.get('status')
            
            # ถ้าเลือกเป็นเสร็จแล้ว หรือ กำลังให้บริการ
            # เราต้องส่งไปหน้าบันทึกบริการเพื่อกรอกบริการและเงินก่อน แล้วถึงจะบันทึกสถานะเป็นเสร็จแล้ว (done) จริงๆ
            if status in ['in_progress', 'done']:
                queue.status = 'in_progress' # เซ็ตเป็นกำลังให้บริการไปก่อน
                queue.save()
                from django.urls import reverse
                return redirect(f"{reverse('service_record_add')}?queue_id={queue.pk}")
            else:
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
            
            queue_id = request.POST.get('queue_id')
            if queue_id:
                if ServiceRecord.objects.filter(queue_id=queue_id).exists():
                    messages.error(request, 'คิวนี้มีการบันทึกบริการไปแล้ว')
                    return redirect('service_record_list')
                try:
                    queue = Queue.objects.get(pk=queue_id)
                    record.queue = queue
                except:
                    pass
                    
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
            
            # เมื่อบันทึกบริการเสร็จแล้ว เปลี่ยนสถานะคิวเป็นเสร็จแล้ว
            if record.queue:
                record.queue.status = 'done'
                record.queue.save()
                
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
        initial_data = {'service_date': timezone.now().date()}
        queue_id = request.GET.get('queue_id')
        
        if queue_id:
            if ServiceRecord.objects.filter(queue_id=queue_id).exists():
                messages.warning(request, 'คิวนี้มีการบันทึกบริการไปแล้ว ไม่สามารถเพิ่มซ้ำได้ (กรุณาใช้ปุ่มแก้ไขแทน)')
                return redirect('service_record_list')
                
            try:
                queue = Queue.objects.get(pk=queue_id)
                initial_data['customer'] = queue.customer
                initial_data['barber'] = queue.barber
            except:
                pass
                
        form = ServiceRecordForm(initial=initial_data)
        
        if not request.user.is_staff and not queue_id:
            try:
                barber = Barber.objects.get(user=request.user)
                form.fields['barber'].initial = barber
            except:
                pass
                
    services = Service.objects.filter(is_active=True)
    return render(request, 'service_record/service_record_form.html', {
        'form': form,
        'services': services,
        'queue_id': request.GET.get('queue_id') or request.POST.get('queue_id')
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
def service_record_edit(request, pk):
    record = ServiceRecord.objects.get(pk=pk)
    if not request.user.is_staff:
        try:
            barber = Barber.objects.get(user=request.user)
            if record.barber != barber:
                return redirect('service_record_list')
        except:
            return redirect('service_record_list')
            
    if request.method == 'POST':
        form = ServiceRecordForm(request.POST, instance=record)
        if form.is_valid():
            edited_record = form.save(commit=False)
            
            # ลบ items เดิมและสร้างใหม่
            edited_record.items.all().delete()
            
            # คำนวณราคารวมใหม่
            service_ids = request.POST.getlist('service_id')
            quantities = request.POST.getlist('quantity')
            total = 0
            for sid, qty in zip(service_ids, quantities):
                try:
                    service = Service.objects.get(pk=sid)
                    total += service.price * int(qty)
                except:
                    pass
            edited_record.total_price = total
            edited_record.save()
            
            # บันทึกรายการบริการ
            for sid, qty in zip(service_ids, quantities):
                try:
                    service = Service.objects.get(pk=sid)
                    ServiceRecordItem.objects.create(
                        record=edited_record,
                        service=service,
                        quantity=int(qty),
                        price=service.price
                    )
                except:
                    pass
            messages.success(request, 'แก้ไขการใช้บริการเรียบร้อยแล้ว')
            return redirect('service_record_list')
    else:
        form = ServiceRecordForm(instance=record)
        
    services = Service.objects.filter(is_active=True)
    existing_items = record.items.all()
    
    return render(request, 'service_record/service_record_form.html', {
        'form': form,
        'services': services,
        'action': 'แก้ไข',
        'existing_items': existing_items
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

from django.db.models import Sum, Count, Q, F

# ===== REPORTS =====
from datetime import timedelta
import json

@login_required(login_url='/login/')
def report_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    # รายได้วันนี้
    today_records = ServiceRecord.objects.filter(service_date=today, is_paid=True)
    today_income = today_records.aggregate(total=Sum('total_price'))['total'] or 0
    
    # รายได้เดือนนี้
    month_records = ServiceRecord.objects.filter(service_date__gte=first_day_of_month, is_paid=True)
    month_income = month_records.aggregate(total=Sum('total_price'))['total'] or 0
    
    # จำนวนคิววันนี้
    today_queues = Queue.objects.filter(appointment_date=today).count()
    
    # จำนวนลูกค้า
    total_customers = Customer.objects.count()
    
    # ช่างที่ทำงานมากสุด
    top_barber = Barber.objects.annotate(
        record_count=Count('servicerecord')
    ).order_by('-record_count').first()
    
    # --- CHART DATA ---
    # 1. Income Last 7 Days (Line Chart)
    income_labels = []
    income_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        income_labels.append(d.strftime('%d %b'))
        daily_total = ServiceRecord.objects.filter(service_date=d, is_paid=True).aggregate(t=Sum('total_price'))['t'] or 0
        income_data.append(float(daily_total))
        
    # 2. Top Services (Donut Chart)
    services = Service.objects.annotate(count=Sum('servicerecorditem__quantity')).filter(count__gt=0).order_by('-count')[:5]
    service_labels = [s.name for s in services]
    service_data = [int(s.count) for s in services]
    
    # 3. Queue Status (Bar Chart)
    q_stats = Queue.objects.values('status').annotate(c=Count('id'))
    q_dict = {item['status']: item['c'] for item in q_stats}
    queue_labels = ['รอคิว', 'กำลังให้บริการ', 'เสร็จแล้ว', 'ยกเลิก']
    queue_data = [q_dict.get('waiting', 0), q_dict.get('in_progress', 0), q_dict.get('done', 0), q_dict.get('cancelled', 0)]
    
    context = {
        'today_income': today_income,
        'month_income': month_income,
        'today_queues': today_queues,
        'total_customers': total_customers,
        'top_barber': top_barber,
        'active_tab': 'dashboard',
        
        # JSON for Charts
        'income_labels': json.dumps(income_labels),
        'income_data': json.dumps(income_data),
        'service_labels': json.dumps(service_labels),
        'service_data': json.dumps(service_data),
        'queue_labels': json.dumps(queue_labels),
        'queue_data': json.dumps(queue_data),
    }
    return render(request, 'report/report_dashboard.html', context)

@login_required(login_url='/login/')
def report_income(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    barber_id = request.GET.get('barber_id')
    
    records = ServiceRecord.objects.filter(is_paid=True).order_by('-service_date')
    
    if not request.user.is_staff:
        try:
            barber = Barber.objects.get(user=request.user)
            records = records.filter(barber=barber)
        except Barber.DoesNotExist:
            records = records.none()
    
    if start_date:
        records = records.filter(service_date__gte=start_date)
    if end_date:
        records = records.filter(service_date__lte=end_date)
    if request.user.is_staff and barber_id:
        records = records.filter(barber_id=barber_id)
        
    total_income = records.aggregate(total=Sum('total_price'))['total'] or 0
    barbers = Barber.objects.all() if request.user.is_staff else []
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response.write('\ufeff'.encode('utf8'))
        response['Content-Disposition'] = 'attachment; filename="income_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['วันที่', 'ลูกค้า', 'ช่าง', 'ยอดรวม (บาท)'])
        
        for r in records:
            writer.writerow([r.service_date.strftime('%Y-%m-%d'), r.customer.name, r.barber.name, r.total_price])
            
        return response
    
    context = {
        'records': records,
        'total_income': total_income,
        'barbers': barbers,
        'active_tab': 'income',
        'start_date': start_date,
        'end_date': end_date,
        'selected_barber': barber_id
    }
    return render(request, 'report/report_income.html', context)

@login_required(login_url='/login/')
def report_barber(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    barbers = Barber.objects.annotate(
        job_count=Count('servicerecord', filter=Q(servicerecord__is_paid=True)),
        customer_count=Count('servicerecord__customer', distinct=True),
        total_income=Sum('servicerecord__total_price', filter=Q(servicerecord__is_paid=True))
    )
    
    context = {
        'barbers': barbers,
        'active_tab': 'barber'
    }
    return render(request, 'report/report_barber.html', context)

@login_required(login_url='/login/')
def report_service(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    services = Service.objects.annotate(
        use_count=Sum('servicerecorditem__quantity'),
        total_income=Sum(F('servicerecorditem__price') * F('servicerecorditem__quantity'))
    ).order_by('-use_count')
    
    service_labels = []
    service_data = []
    total_uses = 0
    for s in services:
        if s.use_count:
            service_labels.append(s.name)
            service_data.append(int(s.use_count))
            total_uses += int(s.use_count)
            
    # Calculate percentages for the template
    for s in services:
        if total_uses > 0 and s.use_count:
            s.percentage = (int(s.use_count) / total_uses) * 100
        else:
            s.percentage = 0
    
    context = {
        'services': services,
        'active_tab': 'service',
        'service_labels': json.dumps(service_labels),
        'service_data': json.dumps(service_data),
    }
    return render(request, 'report/report_service.html', context)

@login_required(login_url='/login/')
def report_queue(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    queues = Queue.objects.all()
    
    if not request.user.is_staff:
        try:
            barber = Barber.objects.get(user=request.user)
            queues = queues.filter(barber=barber)
        except Barber.DoesNotExist:
            queues = queues.none()
            
    if start_date:
        queues = queues.filter(appointment_date__gte=start_date)
    if end_date:
        queues = queues.filter(appointment_date__lte=end_date)
        
    status_summary = queues.values('status').annotate(count=Count('id'))
    summary_dict = {item['status']: item['count'] for item in status_summary}
    
    context = {
        'waiting': summary_dict.get('waiting', 0),
        'in_progress': summary_dict.get('in_progress', 0),
        'done': summary_dict.get('done', 0),
        'cancelled': summary_dict.get('cancelled', 0),
        'active_tab': 'queue'
    }
    return render(request, 'report/report_queue.html', context)

@login_required(login_url='/login/')
def report_purchase(request):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    purchases = PurchaseOrder.objects.all().order_by('-purchase_date')
    
    if start_date:
        purchases = purchases.filter(purchase_date__gte=start_date)
    if end_date:
        purchases = purchases.filter(purchase_date__lte=end_date)
        
    total_spent = sum(p.quantity * p.price_per_unit for p in purchases)
    total_items = sum(p.quantity for p in purchases)
    total_transactions = purchases.count()
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response.write('\ufeff'.encode('utf8'))
        response['Content-Disposition'] = 'attachment; filename="purchase_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['วันที่ซื้อ', 'อุปกรณ์', 'จำนวน', 'ราคา/หน่วย', 'รวม (บาท)', 'หมายเหตุ'])
        
        for p in purchases:
            total = p.quantity * p.price_per_unit
            writer.writerow([p.purchase_date.strftime('%Y-%m-%d'), p.equipment.name, f"{p.quantity} {p.equipment.unit}", p.price_per_unit, total, p.note])
            
        return response
    
    context = {
        'purchases': purchases,
        'total_spent': total_spent,
        'total_items': total_items,
        'total_transactions': total_transactions,
        'start_date': start_date,
        'end_date': end_date,
        'active_tab': 'purchase'
    }
    return render(request, 'report/report_purchase.html', context)