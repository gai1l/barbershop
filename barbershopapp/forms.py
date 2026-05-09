from django import forms
from django.contrib.auth.models import User
from .models import Barber, Customer, Service, Equipment

# ===== BARBER FORM =====
class BarberForm(forms.ModelForm):
    username = forms.CharField(
        label='ชื่อผู้ใช้ (สำหรับ Login)',
        max_length=150
    )
    password = forms.CharField(
        label='รหัสผ่าน',
        widget=forms.PasswordInput,
        required=False,
        help_text='ถ้าไม่ต้องการเปลี่ยนรหัสผ่าน ให้เว้นว่างไว้'
    )

    class Meta:
        model = Barber
        fields = ['name', 'phone', 'photo', 'is_active']
        labels = {
            'name': 'ชื่อช่าง',
            'phone': 'เบอร์โทร',
            'photo': 'รูปภาพ',
            'is_active': 'ใช้งานอยู่',
        }

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.pop('instance_user', None)
        super().__init__(*args, **kwargs)
        if self.instance_user:
            self.fields['username'].initial = self.instance_user.username
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.update({'class': 'form-control'})

# ===== CUSTOMER FORM =====
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email']
        labels = {
            'name': 'ชื่อลูกค้า',
            'phone': 'เบอร์โทร',
            'email': 'อีเมล',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

# ===== SERVICE FORM =====
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'price', 'duration', 'is_active']
        labels = {
            'name': 'ชื่อบริการ',
            'price': 'ราคา (บาท)',
            'duration': 'ระยะเวลา (นาที)',
            'is_active': 'ใช้งานอยู่',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.update({'class': 'form-control'})

# ===== EQUIPMENT FORM =====
class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'unit', 'min_stock']
        labels = {
            'name': 'ชื่ออุปกรณ์',
            'unit': 'หน่วย',
            'min_stock': 'สต็อกขั้นต่ำ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            
from .models import Barber, Customer, Service, Equipment, PurchaseOrder

# ===== PURCHASE FORM =====
class PurchaseForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['equipment', 'quantity', 'price_per_unit', 'purchase_date', 'note']
        labels = {
            'equipment': 'อุปกรณ์',
            'quantity': 'จำนวนที่ซื้อ',
            'price_per_unit': 'ราคาต่อหน่วย (บาท)',
            'purchase_date': 'วันที่ซื้อ',
            'note': 'หมายเหตุ',
        }
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['purchase_date', 'note']:
                field.widget.attrs.update({'class': 'form-control'})