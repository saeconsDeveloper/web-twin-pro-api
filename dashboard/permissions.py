from rest_framework import permissions

# from django.contrib.auth.models import Group

class SuperAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        required_group = 'Superadmin'
        return request.user.groups.filter(name=required_group).exists()

class UberAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        required_group = 'Uberadmin'
        return request.user.groups.filter(name=required_group).exists()
    
class DeveloperPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        required_group = 'Developer'
        return request.user.groups.filter(name=required_group).exists()

class ExperienceDesignerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        required_group = 'Experience Designer'
        return request.user.groups.filter(name=required_group).exists()

class ViewerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        required_group = 'Viewer'
        return request.user.groups.filter(name=required_group).exists()
    
class ProductManagerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        required_group = 'Product Manager'
        return request.user.groups.filter(name=required_group).exists()
