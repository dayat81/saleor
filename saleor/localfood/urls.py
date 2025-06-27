"""
URL configuration for Local Food debug endpoints.
"""
from django.urls import path
from . import debug_utils

app_name = 'localfood'

urlpatterns = [
    path('debug/status/', debug_utils.debug_status, name='debug_status'),
    path('debug/trigger-task/', debug_utils.debug_trigger_task, name='debug_trigger_task'),
    path('debug/create-test-data/', debug_utils.debug_create_test_data, name='debug_create_test_data'),
    path('debug/graphql-info/', debug_utils.debug_graphql_info, name='debug_graphql_info'),
]