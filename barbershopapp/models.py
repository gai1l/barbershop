from django.db import models
from django.contrib.auth.models import User

class Barber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name='ชื่อช่าง')
    phone = models.CharField(max_length=20, verbose_name='เบอร์โทร')
    photo = models.ImageField(upload_to='barbers/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ช่าง'
        verbose_name_plural = 'ช่าง'

class Customer(models.Model):
    name = models.CharField(max_length=100, verbose_name='ชื่อลูกค้า')
    phone = models.CharField(max_length=20, verbose_name='เบอร์โทร')
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ลูกค้า'
        verbose_name_plural = 'ลูกค้า'

class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name='ชื่อบริการ')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='ราคา')
    duration = models.IntegerField(default=30, verbose_name='เวลา (นาที)')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'บริการ'
        verbose_name_plural = 'บริการ'

class Equipment(models.Model):
    name = models.CharField(max_length=100, verbose_name='ชื่ออุปกรณ์')
    unit = models.CharField(max_length=20, verbose_name='หน่วย')
    stock = models.IntegerField(default=0, verbose_name='จำนวนคงเหลือ')
    min_stock = models.IntegerField(default=5, verbose_name='สต็อกขั้นต่ำ')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'อุปกรณ์'
        verbose_name_plural = 'อุปกรณ์'

class PurchaseOrder(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, verbose_name='อุปกรณ์')
    quantity = models.IntegerField(verbose_name='จำนวนที่ซื้อ')
    price_per_unit = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='ราคาต่อหน่วย')
    purchase_date = models.DateField(verbose_name='วันที่ซื้อ')
    note = models.TextField(null=True, blank=True, verbose_name='หมายเหตุ')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.equipment.name} x{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.equipment.stock += self.quantity
            self.equipment.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'รายการซื้ออุปกรณ์'
        verbose_name_plural = 'รายการซื้ออุปกรณ์'

class Queue(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'รอคิว'),
        ('in_progress', 'กำลังให้บริการ'),
        ('done', 'เสร็จแล้ว'),
        ('cancelled', 'ยกเลิก'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='ลูกค้า')
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, verbose_name='ช่าง')
    appointment_date = models.DateField(verbose_name='วันนัด')
    appointment_time = models.TimeField(verbose_name='เวลานัด')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name='สถานะ')
    note = models.TextField(null=True, blank=True, verbose_name='หมายเหตุ')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} - {self.barber.name} ({self.appointment_date})"

    class Meta:
        verbose_name = 'คิว'
        verbose_name_plural = 'คิว'

class ServiceRecord(models.Model):
    queue = models.OneToOneField(Queue, on_delete=models.CASCADE, null=True, blank=True, verbose_name='คิว')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='ลูกค้า')
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE, verbose_name='ช่าง')
    service_date = models.DateField(verbose_name='วันที่บริการ')
    is_paid = models.BooleanField(default=False, verbose_name='ชำระเงินแล้ว')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='ราคารวม')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.name} ({self.service_date})"

    class Meta:
        verbose_name = 'บันทึกการใช้บริการ'
        verbose_name_plural = 'บันทึกการใช้บริการ'

class ServiceRecordItem(models.Model):
    record = models.ForeignKey(ServiceRecord, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='บริการ')
    quantity = models.IntegerField(default=1, verbose_name='จำนวน')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='ราคา')

    def __str__(self):
        return f"{self.service.name} x{self.quantity}"

    class Meta:
        verbose_name = 'รายการบริการ'
        verbose_name_plural = 'รายการบริการ'