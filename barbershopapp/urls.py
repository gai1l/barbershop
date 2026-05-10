from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Process 2 — ข้อมูลพื้นฐาน
    path('barbers/', views.barber_list, name='barber_list'),
    path('barbers/add/', views.barber_add, name='barber_add'),
    path('barbers/edit/<int:pk>/', views.barber_edit, name='barber_edit'),
    path('barbers/delete/<int:pk>/', views.barber_delete, name='barber_delete'),

    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('customers/delete/<int:pk>/', views.customer_delete, name='customer_delete'),

    path('services/', views.service_list, name='service_list'),
    path('services/add/', views.service_add, name='service_add'),
    path('services/edit/<int:pk>/', views.service_edit, name='service_edit'),
    path('services/delete/<int:pk>/', views.service_delete, name='service_delete'),

    path('equipments/', views.equipment_list, name='equipment_list'),
    path('equipments/add/', views.equipment_add, name='equipment_add'),
    path('equipments/edit/<int:pk>/', views.equipment_edit, name='equipment_edit'),
    path('equipments/delete/<int:pk>/', views.equipment_delete, name='equipment_delete'),

    # Process 3 — ซื้ออุปกรณ์
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_add, name='purchase_add'),
    path('purchases/delete/<int:pk>/', views.purchase_delete, name='purchase_delete'),

    # Process 4 — คิว
    path('queues/', views.queue_list, name='queue_list'),
    path('queues/add/', views.queue_add, name='queue_add'),
    path('queues/edit/<int:pk>/', views.queue_edit, name='queue_edit'),
    path('queues/status/<int:pk>/', views.queue_update_status, name='queue_update_status'),
    path('queues/delete/<int:pk>/', views.queue_delete, name='queue_delete'),
    
    # Process 5 — บันทึกการใช้บริการ
    path('records/', views.service_record_list, name='service_record_list'),
    path('records/add/', views.service_record_add, name='service_record_add'),
    path('records/detail/<int:pk>/', views.service_record_detail, name='service_record_detail'),
    path('records/pay/<int:pk>/', views.service_record_pay, name='service_record_pay'),
    path('records/delete/<int:pk>/', views.service_record_delete, name='service_record_delete'),
]