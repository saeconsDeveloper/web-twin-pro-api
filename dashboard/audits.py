from django.core import serializers

from .models import AuditTrail

# AUDIT_CHOICES = {a[1]: a[0] for a in AUDIT_TYPE_CHOICES}

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# def store_audit(*,request, instance, action, previous_instance=None):
#     audit = AuditTrail()
#     audit.model_type = instance._meta.verbose_name.title()
#     audit.object_id = instance.id
#     audit.object_str = instance.title
#     audit.action = action
#     audit.user = request.user
#     audit.ip = get_client_ip(request)
#     audit.instance = serializers.serialize("json", [instance])
#     if previous_instance:
#         audit.previous_instance = previous_instance.instance
#     audit.save()

def store_audit(*, request, instance, action, previous_instance=None, settings_object=None, obj=None):
    
    audit = AuditTrail()
    audit.model_type = instance._meta.verbose_name.title()
    audit.object_id = instance.pk
    audit.object_str = str(instance) if settings_object is None else str(settings_object)
    audit.action = action
    audit.user = request.user
    audit.ip = get_client_ip(request)
    audit.instance = serializers.serialize("json", [instance])
    if previous_instance:
        audit.previous_instance = previous_instance.instance
    audit.save()
