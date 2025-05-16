# myapi/urls.py
from django.urls import path
from .views import upload_data, get_result_all, get_hardware_data, get_model_data, get_mode_data, get_score_suggestion, \
    get_hardware_all, get_model_all, get_mode_all, get_baseline_id

urlpatterns = [
    path('upload_data', upload_data),
    path('get_result_all', get_result_all),
    path('get_hardware_data', get_hardware_data),
    path('get_model_data', get_model_data),
    path('get_mode_data', get_mode_data),
    path('get_score_suggestion', get_score_suggestion),
    path('get_hardware_all', get_hardware_all),
    path('get_model_all', get_model_all),
    path('get_mode_all', get_mode_all),
    path('get_baseline_id', get_baseline_id),
]