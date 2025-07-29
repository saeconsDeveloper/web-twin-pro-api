from django.contrib.auth.models import User
from django.http import Http404, HttpResponseNotAllowed
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated , IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from django.shortcuts import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Prefetch
import json
from django.core.mail import send_mail
from django.conf import settings


from .audits import store_audit
from .models import (
    AuditTrail,
    CallToActionPro,
    FilterIcon,
    HomePageOption,
    ProductPanel,
    ProductTier1,
    Scene,
    Sector,
    SiteConfig,
    ThemeOption,
    UnityScene,
    User,
    FileLibrary,
    Model3D,
    ShareIcon,
    ActionType,
    SceneGroup,
    UnitySceneVersion
)
from .permissions import (
    DeveloperPermission,
    ProductManagerPermission,
    SuperAdminPermission,
    UberAdminPermission,
    ExperienceDesignerPermission
)
from .serializers import (
    HomePageSerializer,
    HomePageUpdateSerializer,
    FilterIconSerializer,
    FilterIconUpdateSerializer,
    InteractionsSerializer,
    ProductAddUpdateSerializer,
    ProductCategoriesCreateSerializer,
    ProductCategoriesSerializer,
    ProductSerializer,
    SceneCategoriesCreateSerializer,
    SceneCategoriesSerializer,
    SceneCreateSerializer,
    SceneSerializer,
    SettingsSerializer,
    SettingsUpdateSerializer,
    UnitySceneCreateSerializer,
    UnitySceneSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    FileLibrarySerializer,
    Model3DSerializer,
    FileLibraryUpdateSerializer,
    SceneDetailSerializer,
    ProductCategoriesDetailSerializer,
    AuditTrailSerializer,
    SceneDropdownSerializer,
    SceneCategoriesDropdownSerializer,
    UnitySceneDropdownSerializer,
    ProductDropdownSerializer,
    ProductCategoryDropdownSerializer,
    InteractionsDropdownSerializer,
    InteractionsCreateSerializer,
    SceneUpdateSerializer,
    ShareIconSerializer,
    # ShareIconUpdateSerializer,
    FilterActionSerializer,
    SceneGroupSerializer,
    ProductCategoriesUpdateSerializer,
    InteractionsUpdateSerializer,
    InteractionsDetailSerializer,
    ProductDetailSerializer,
    SceneCategoriesFilterSerializer,
    SceneSerializerImmersiveON,
    UnitySceneVersionSerializer,
    UnitySceneVersionCreateSerializer,
    SceneCategorySerializer,


)
from .utils import reset_user_password
from rest_framework.exceptions import AuthenticationFailed


class CustomAPIView(APIView):
    def handle_exception(self, exc):
        if isinstance(exc, AuthenticationFailed):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_403_FORBIDDEN)
        return super().handle_exception(exc)

# ---------------------------------------------------------------------------------------------------------
# AUDITS
# ---------------------------------------------------------------------------------------------------------

class AuditListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):
        instance = AuditTrail.objects.order_by("-updated_at")

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(instance, request)

        serializer = AuditTrailSerializer(paginated_data, many=True)
        count = instance.count()

        response_data = {
                'data': serializer.data,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'total':count
            }
        
        return Response(response_data)


# ---------------------------------------------------------------------------------------------------------
# SEARCH
# ---------------------------------------------------------------------------------------------------------
class SearchView(APIView):
        
    def dispatch(self, request, *args, **kwargs):
        settings = SiteConfig.objects.first()
        
        if not settings:
            settings = SiteConfig.objects.create()

        if settings.browse_without_login:
            self.authentication_classes = []
            self.permission_classes = []
        else:
            self.authentication_classes = [JWTAuthentication]
            self.permission_classes = [IsAuthenticated]
            
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):

        scene = Scene.objects.filter(deleted_at__isnull=True)
        scene_category = Sector.objects.filter(deleted_at__isnull=True)
        product = ProductPanel.objects.filter(deleted_at__isnull=True)

        key_query = request.query_params.get('key')

        try:
            scene_data = scene.filter(title__icontains=key_query)
            category_data = scene_category.filter(name__icontains=key_query)
            product_data = product.filter(display_text__icontains=key_query)
            
            scene_serilaizer = SceneDetailSerializer(scene_data, many=True)
            category_serializer = SceneCategoriesSerializer(category_data, many=True)
            product_serializer = ProductSerializer(product_data, many=True)
            
            response_data = {
                "scene":scene_serilaizer.data,
                "scene_category":category_serializer.data,
                "product":product_serializer.data
            }
            return Response({"data":response_data})
        
        except:
            raise Http404

# ---------------------------------------------------------------------------------------------------------
# CONTACT US
# ---------------------------------------------------------------------------------------------------------

class ContactUs(CustomAPIView):
    def post(self, request):

        body = json.loads(request.body)
        full_name = body['data']['full_name']
        email = body['data']['email']
        message = body['data']['message']

        msg = """
            You have received a new message.<br><br>
            <strong>Full Name:</strong> {full_name}<br>
            <strong>Email:</strong> {email}<br>
            <strong>Message:</strong><br>
            {message}
        """.format(
            full_name=full_name,
            email=email,
            message=message,
        )
        try:       
            send_mail(
                    subject="New message from {}".format(full_name),
                    message="",
                    from_email="{} <{}>".format(
                        settings.EMAIL_DISPLAY_NAME, settings.DEFAULT_FROM_EMAIL
                    ),
                    # recipient_list=SiteConfig.get_instance().contact_form_recipients
                    # if SiteConfig.get_instance().contact_form_recipients
                    # else None,
                    recipient_list=settings.EMAIL_RECIPENT_LIST,
                    html_message=msg,
                    fail_silently=True,
                )
            return Response({"message": "email successfully sent"}, status=200)
        except:
            return Response({"message": "email failed"}, status=400)


# ---------------------------------------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------------------------------------

class UserView(CustomAPIView):

    def dispatch(self, request, *args, **kwargs):
        settings = SiteConfig.objects.first()
        
        if not settings:
            settings = SiteConfig.objects.create()

        if settings.browse_without_login:
            self.authentication_classes = [JWTAuthentication]
            self.permission_classes = []
        else:
            self.authentication_classes = [JWTAuthentication]
            self.permission_classes = [IsAuthenticated]
            
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):

        settings = SiteConfig.objects.first()
        if not settings:
            settings = SiteConfig.objects.create()
        
        browse_without_login = settings.browse_without_login
        title = settings.title
        user = request.user
        print(request.auth)
        if not request.auth and browse_without_login:
            data = {
            'role' : ["Viewer"]
        }
            return Response({"data":data})
        else:
            data = {
                'name': user.get_full_name(),
                'email': user.email or user.username,
                'title': title,
                'role' : [group.name for group in user.groups.all()]
            }
            return Response({"data":data})


class UserListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):

        first_name_query = request.query_params.get('first_name')
        last_name_query = request.query_params.get('last_name')
        role_query = request.query_params.get('role')

        user = User.objects.order_by("-date_joined").filter(is_superuser = False)

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(user, request)

        serializer = UserSerializer(paginated_data, many=True)
        count = user.count()

        response_data = {
                'data': serializer.data,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'total':count
            }

        if first_name_query or last_name_query or role_query:
            if first_name_query:
                queryset = user.filter(first_name__icontains=first_name_query)
            if last_name_query:
                queryset = user.filter(last_name__icontains=last_name_query)
            if role_query:
                queryset = user.filter(groups__name__icontains=role_query)
            
            paginated_data = paginator.paginate_queryset(queryset, request)    

            serializer = UserSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
                    'data': serializer.data,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total': count
                }

            return Response(response_data)

        return Response(response_data)


class UserCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            store_audit(
                request=self.request,
                instance=data,
                action="CREATE"
            )
            return Response({"response": {
                "success": "user created succesfully"
            }}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserUpdateView(generics.UpdateAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return User.objects.get(id=pk)
        except User.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = UserUpdateSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserStatusView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def post(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except Exception as e:
            return Response({"error": str(e)})

        if user.is_active == True:
            user.is_active = False
        else:
            user.is_active = True

        user.save()

        return Response({"response": "sucessfully changed user status"})


class UserPasswordResetView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def post(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({"error": "user with this id doesn't exist."})
        reset_user_password(user)
        return Response({"message": "successfully sent a password reset link to the given email address."})

# ---------------------------------------------------------------------------------------------------------
# SCENES CRUD
# ---------------------------------------------------------------------------------------------------------


class SceneListView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):

        title_query = request.query_params.get('title')
        slug_query = request.query_params.get('slug')
        status_query = request.query_params.get('status')
        scene_category_id = request.query_params.get('scene_category_id')

        dropdown = request.query_params.get('dropdown')

        scene = Scene.objects.filter(
            deleted_at__isnull=True).order_by("priority","-created_at")
        
        count = scene.count()

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(scene, request)

        settings = SiteConfig.objects.first()
        if settings.immersive_experience:

            if not settings.default_scene:
                settings.default_scene = Scene.objects.first()
                settings.save()

            serializer = SceneSerializerImmersiveON(paginated_data, many=True)
        else:
            serializer = SceneSerializer(paginated_data, many=True)

        response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }

        if scene_category_id is not None:
            try:
                scene_category = Sector.objects.get(id=scene_category_id)
            except Exception:
                scene_category = None
                return Response({"scene_category_id":['scene category with that id doesnot exist']}, status=status.HTTP_400_BAD_REQUEST)
            
            if scene_category: 
                scene = Scene.objects.filter(sectors_and_departments=scene_category)
                serializer = SceneSerializer(scene, many=True)
                count = scene.count()
                
            response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total':count
            }

            return Response(response_data)
                
        if dropdown is not None:
            serializer = SceneDropdownSerializer(scene, many=True)
            return Response({"data":serializer.data})
        
        if title_query or slug_query or status_query:
            if title_query:
                queryset = scene.filter(title__icontains=title_query)
            if slug_query:
                queryset = scene.filter(slug__icontains=slug_query)
            if status_query:
                queryset = scene.filter(status=status_query)

            paginated_data = paginator.paginate_queryset(queryset, request)

            serializer = SceneSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
                'data': serializer.data,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'total': count
                }

            return Response(response_data)

        return Response(response_data)
    

class SceneDetailView(CustomAPIView):
    
    def get_object(self, pk):
        try:
            return Scene.objects.get(id=pk)
        except Scene.DoesNotExist:
            raise Http404
    
    def dispatch(self, request, *args, **kwargs):
        settings = SiteConfig.objects.first()
        if settings.browse_without_login:
            self.authentication_classes = []
            self.permission_classes = []
        else:
            self.authentication_classes = [JWTAuthentication]
            self.permission_classes = [IsAuthenticated,
                                        (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
        return super().dispatch(request, *args, **kwargs)
        
    def get(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = SceneDetailSerializer(instance)
        return Response({"data":serializer.data})


class SceneSlugDetails(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
    
    def get_slug(self, slug):
        try:
            return Scene.objects.get(slug=slug)
        except Scene.DoesNotExist:
            raise Http404
    
    def get(self, request, slug, *args, **kwargs):
        instance = self.get_slug(slug)
        serializer = SceneDetailSerializer(instance)
        return Response({"data":serializer.data})
    

class SceneCreateView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def post(self, request):
        serializer = SceneCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            store_audit(
                request=self.request,
                instance=data,
                action="CREATE"
            )
            return Response({"message": "scene successfully created"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SceneUpdateView(generics.UpdateAPIView, CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return Scene.objects.get(id=pk)
        except Scene.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = SceneUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            data = serializer.save()
            try:
                prev_obj = AuditTrail.objects.filter(
                    object_id=instance.id).order_by('-created_at')[0]
            except:
                prev_obj = None
            store_audit(
                request=self.request,
                instance=data,
                action="UPDATE",
                previous_instance=prev_obj
            )
            return Response({"message" : "scene successfully updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SceneDeleteView(generics.DestroyAPIView, CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return Scene.objects.get(id=pk)
        except Scene.DoesNotExist:
            raise Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        
        settings = SiteConfig.objects.first()

        if not settings:
            settings = SiteConfig.objects.first()

        if settings.default_scene == instance:
            return Response({"error":"unable to delete this scene as it is default scene for immersive experience"}, status=status.HTTP_400_BAD_REQUEST)

        if instance.deleted_at is not None:
            return Response({"message": "scene already deleted"}, status=status.HTTP_200_OK)
        instance.geography = None
        instance.save(update_fields=["geography"])
        self.perform_destroy(instance)
        store_audit(
            request=self.request,
            instance=self.get_object(pk),
            action="DELETE",
            previous_instance=AuditTrail.objects.filter(
                object_id=pk).order_by('-created_at')[0]
        )
        return Response({"message": "scene deleted successfully"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------------------------------------
# SCENE CATEGORIES
# ---------------------------------------------------------------------------------------------------------

class SceneCategoriesListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
    
    def dispatch(self, request, *args, **kwargs):
        settings = SiteConfig.objects.first()
        
        if not settings:
            settings = SiteConfig.objects.create()

        if settings.browse_without_login:
            self.authentication_classes = []
            self.permission_classes = []
        else:
            self.authentication_classes = [JWTAuthentication]
            self.permission_classes = [IsAuthenticated,
                                        (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):

        name_query = request.query_params.get('name')
        status_query = request.query_params.get('status')
        dropdown = request.query_params.get('dropdown')

        data = Sector.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(data, request)

        serializer = SceneCategoriesSerializer(paginated_data, many=True)
        count = data.count()

        response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }
        
        if dropdown is not None:
            serializer = SceneCategoriesDropdownSerializer(data, many=True)
            return Response({"data":serializer.data})
        else:
            pass
    
        if name_query or status_query:
            if name_query:
                queryset = data.filter(name__icontains=name_query)
            if status_query:
                queryset = data.filter(status=status_query)

            paginated_data = paginator.paginate_queryset(queryset, request)

            serializer = SceneCategoriesSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
                    'data': serializer.data,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total': count
                }

            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(response_data)


class SceneCategoriesDetailView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
    
    def dispatch(self, request, *args, **kwargs):
        settings = SiteConfig.objects.first()
        
        if not settings:
            settings = SiteConfig.objects.create()

        if settings.browse_without_login:
            self.authentication_classes = []
            self.permission_classes = []
        else:
            self.authentication_classes = [JWTAuthentication]
            self.permission_classes = [IsAuthenticated]
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_sector(self, pk):
        try:
            return Sector.objects.get(id=pk)
        except Sector.DoesNotExist:
            return Http404

    def get(self, request, pk):
        instance = self.get_sector(pk)
        obj = Scene.objects.filter(sectors_and_departments=pk, deleted_at__isnull=True)
        relatedSceneQuery = request.query_params.get('related-scenes')

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(obj, request)

        if relatedSceneQuery is not None:
            
            scene_serializer = SceneCategorySerializer(paginated_data, many=True)

            grouped_items = {}
          
            for item in scene_serializer.data:
                scene_group = item['scene_group']
                item_id = item['id']
                
                if scene_group is None:
                    grouped_items['NONE'] = []
                    grouped_items['NONE'].append(item_id)
                 
                if scene_group:
                    scene_group_id = item['scene_group']['id'] 
                                    
                    if scene_group_id in grouped_items:
                        grouped_items[scene_group_id].append(item_id)
                    else:
                        grouped_items[scene_group_id] = [item_id]
            first_items = {}
           
            for scene_group_id, items in grouped_items.items():
                scene_id = items[0]
                first_items[scene_group_id] = scene_id
    
            child_scene_IDs = []
    
            for group_id, items in grouped_items.items():
                if len(items) >= 1:
                    if group_id == 'NONE':
                        group_items = {
                        'scene_group_id': 'NONE',
                        'scene_id': items[0:]  
                        }
                    else:
                        group_items = {
                            'scene_group_id': group_id,
                            'scene_id': items[1:]  
                        }
                    child_scene_IDs.append(group_items)

            response_list = []
            
            for scene_group_id, scene_id in first_items.items():
                child_scene_list = []
                scene = Scene.objects.get(id=scene_id)
                serializer = SceneCategorySerializer(scene)
                for item in child_scene_IDs:
                    child_scene_group_id = item['scene_group_id']
                    child_scene_id = item['scene_id']
                    if child_scene_group_id == 'NONE':
                        for obj in child_scene_id:
                            scene = Scene.objects.get(id=obj)
                            serializerForSceneGroup = SceneSerializer(scene)
                            response_list.append(serializer.data)
                    elif scene_group_id == child_scene_group_id:
                        for obj in child_scene_id:
                            scene = Scene.objects.get(id=obj)
                            serializerForSceneGroup = SceneSerializer(scene)
                            child_scene_list.append(serializerForSceneGroup.data)
                        serializer.data['scene_group']['related_scene_group'] = child_scene_list
                        response_list.append(serializer.data)

            unique_data = []
            seen_ids = set()

            for item in response_list:
                item_id = item['id']
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_data.append(item)
                    
            response_data = {
                "data": unique_data,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link()
            }
            return Response(response_data)

        serializer = SceneCategoriesSerializer(instance)
        # serializer = SceneSerializer(paginated_data, many=True)
        response_data = {
            'data': serializer.data
        }

        return Response(response_data)        


class SceneCategoriesCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def post(self, request):
        serializer = SceneCategoriesCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "success", "data": (serializer.data)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SceneCategoriesUpdateView(generics.UpdateAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return Sector.objects.get(id=pk)
        except Sector.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = SceneCategoriesSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"successfully updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SceneCategoriesDeleteView(generics.DestroyAPIView, CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return Sector.objects.get(id=pk)
        except Sector.DoesNotExist:
            raise Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        self.perform_destroy(instance)
        return Response({"message": "scene category deleted successfully"}, status=status.HTTP_200_OK)
    

class SceneCategoriesFilter(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
    
    def get(self, request):
        instance = Sector.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")
        serializer = SceneCategoriesFilterSerializer(instance, many=True)
        return Response({"data":serializer.data})
    
    def post(self, request):
        body = json.loads(request.body)
        id = body["data"]["id"]
        
        if not all(Sector.objects.filter(id=i, deleted_at__isnull=True).exists() for i in id):
            return Response({"error": "valid id not provided"})
    
        for obj in Sector.objects.filter(id__in=id, deleted_at__isnull=True):
            obj.show_in_filter = not obj.show_in_filter
            obj.save()
    
        return Response({"message": "success"})


# ---------------------------------------------------------------------------------------------------------
# UNITY SCENE CRUD
# ---------------------------------------------------------------------------------------------------------


class UnitySceneListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated, ( SuperAdminPermission | UberAdminPermission | DeveloperPermission | IsAdminUser |  ExperienceDesignerPermission | DeveloperPermission)]

    def get(self, request):
        name_query = request.query_params.get('name')
        dropdown = request.query_params.get('dropdown')
        scene_id = request.query_params.get('scene_id')

        dropdown_settings = request.query_params.get('dropdown-settings')

        unity_scene = UnityScene.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(unity_scene, request)

        serializer = UnitySceneSerializer(paginated_data, many=True)
        count = unity_scene.count()

        data = []

        for unitySceneItem in serializer.data:
            id = unitySceneItem['id']
            try:
                obj = Scene.objects.get(unity_scene=id)
            except Scene.DoesNotExist:
                obj = None
                
            if obj:
                related_scene = {
                    "id":obj.id,
                    "name":obj.title
                }
            else:
                related_scene = None

            unitySceneObj = {
                "id":unitySceneItem['id'],
                "name":unitySceneItem['name'],
                "background_image":unitySceneItem['background_image'],
                "loading_text":unitySceneItem['loading_text'],
                "unity_file":unitySceneItem['unity_file'],
                "related_scene":related_scene
                }

            data.append(unitySceneObj)

        response_data = {
            'data': data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count 
            }
        
        used_unity_scenes = []
        free_unity_scenes = []

        if dropdown is not None:
            scene = Scene.objects.filter(deleted_at__isnull=True)

            if scene_id is not None:
                try:
                    obj = Scene.objects.get(id = scene_id)
                except Scene.DoesNotExist:
                    obj = None
                if obj:
                    if obj.unity_scene:
                        serializer = UnitySceneDropdownSerializer(obj.unity_scene)
                        free_unity_scenes.append(serializer.data)

            for i in scene:
                for j in unity_scene:
                    if i.unity_scene == j:
                        used_unity_scenes.append(j.id)

            for i in unity_scene:
                if i.id not in used_unity_scenes:
                    serializer = UnitySceneDropdownSerializer(i)
                    free_unity_scenes.append(serializer.data)

            return Response({"data":free_unity_scenes})
        
        elif scene_id is not None:
                try:
                    obj = Scene.objects.get(id = scene_id)
                except Scene.DoesNotExist:
                    obj = None
                if obj:
                    if obj.unity_scene:
                        serializer = UnitySceneSerializer(obj.unity_scene)
                        return Response({"data":serializer.data})

        if dropdown_settings is not None:
            serializer = UnitySceneDropdownSerializer(unity_scene, many=True)
            return Response({"data":serializer.data})
        
        if name_query:
            queryset = unity_scene.filter(name__icontains=name_query)
            paginated_data = paginator.paginate_queryset(queryset, request)

            serializer = UnitySceneSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }

            return Response(response_data)

        return Response(response_data)


class UnitySceneCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | ExperienceDesignerPermission | DeveloperPermission)]

    def post(self, request):
        serializer = UnitySceneCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unity Scene Created", "data": (serializer.data)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitySceneUpdateView(generics.UpdateAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | DeveloperPermission )]

    def get_object(self, pk):
        try:
            return UnityScene.objects.get(id=pk)
        except UnityScene.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = UnitySceneSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "success", "data": (serializer.data)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitySceneDeleteView(generics.DestroyAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | DeveloperPermission )]

    def get_object(self, pk):
        try:
            return UnityScene.objects.get(id=pk)
        except UnityScene.DoesNotExist:
            raise Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)

        settings = SiteConfig.objects.first()

        if not settings:
            settings = SiteConfig.objects.create()

        if settings.default_scene:
            scene_id = settings.default_scene.id
            scene = Scene.objects.get(id=scene_id)
            unity_scene = scene.unity_scene
            if unity_scene == instance:
                return Response({"error":"cannot delete this unity scene as it is associated with a scene that is selected for immersive experience"}, status=status.HTTP_400_BAD_REQUEST)

        self.perform_destroy(instance)
        return Response({"message": "unityscene deleted successfully"}, status=status.HTTP_200_OK)
    

# ---------------------------------------------------------------------------------------------------------
# UNITY SCENES VERSION
# ---------------------------------------------------------------------------------------------------------
class UnitySceneVersionListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | DeveloperPermission | ExperienceDesignerPermission )]
    
    def get_object(self, pk):
        try:
            return UnitySceneVersion.objects.filter(unity_scene=pk, deleted_at__isnull = True).order_by("-created_at")
        except UnitySceneVersion.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        instance = self.get_object(pk)
        serializer = UnitySceneVersionSerializer(instance, many=True)
        return Response({'data':serializer.data})
        

class UnitySceneVersionCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | DeveloperPermission | ExperienceDesignerPermission )]
    
    def get_unity_scene(self, pk):
        try:
            return UnityScene.objects.get(id=pk, deleted_at__isnull = True)
        except UnityScene.DoesNotExist:
            return None
    
    def post(self, request, pk):
        unity_scene = self.get_unity_scene(pk)
        if unity_scene is None:
             return Response({'detail': 'Unity scene not found'}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data.get('data', {}) 
        data['unity_scene'] = unity_scene.id
        serializer = UnitySceneVersionCreateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message':"successfully created version for the unity scene"}, status=status.HTTP_200_OK)
        return Response({"message":"version creation failed"}, status=status.HTTP_400_BAD_REQUEST)
    

class UnitySceneVersionUpdateView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | DeveloperPermission | ExperienceDesignerPermission )]
    
    def get_version(self, version_id):
        try:
            return UnitySceneVersion.objects.get(id=version_id)
        except UnitySceneVersion.DoesNotExist:
            raise Http404
    
    def get_unity_scene(self, pk):
        try:
            return UnityScene.objects.get(id=pk)
        except UnityScene.DoesNotExist:
            raise Http404

    def put(self, request, pk, version_id, *args, **kwargs):
        data = request.data.get('data', {}) 
        version = self.get_version(version_id)
        unity_scene = self.get_unity_scene(pk)
        if not version.unity_scene == unity_scene:
            return Response({"error":"the version is not related to this unity scene"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UnitySceneVersionSerializer(
            instance=version, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "successfully updated the version"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ---------------------------------------------------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------------------------------------------------

class ProductListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated, (SuperAdminPermission | UberAdminPermission | ProductManagerPermission | IsAdminUser)]

    def get(self, request):
        name_query = request.query_params.get('name')
        status_query = request.query_params.get('status')
        dropdown = request.query_params.get('dropdown')
        
        product = ProductPanel.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")
        
        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(product, request)

        serializer = ProductSerializer(paginated_data, many=True)
        count = product.count()

        response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }

        if dropdown is not None:
            serializer = ProductDropdownSerializer(product, many=True)
            return Response({"data":serializer.data})
        else:
            pass

                  
        if name_query or status_query:
            if name_query:
                queryset = product.filter(display_text__icontains=name_query)
            if status_query:
                queryset = product.filter(status=status_query)
                
            paginated_data = paginator.paginate_queryset(queryset, request)
            
            serializer = ProductSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }
            return Response(response_data)
        
        return Response(response_data)


class ProductDetailView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated, (SuperAdminPermission | UberAdminPermission | ProductManagerPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return ProductPanel.objects.get(id=pk)
        except ProductPanel.DoesNotExist:
            raise Http404

    def get(self, request, pk):

        product = self.get_object(pk)
        serializer = ProductDetailSerializer(product)

        return Response({"data": (serializer.data)})


class ProductCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated, (SuperAdminPermission | UberAdminPermission | ProductManagerPermission | IsAdminUser)]

    def post(self, request):
        serializer = ProductAddUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save_with_position()
            return Response({"message": "product created", "data": (serializer.data)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductUpdateView(generics.UpdateAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated, (SuperAdminPermission | UberAdminPermission | ProductManagerPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return ProductPanel.objects.get(id=pk)
        except ProductPanel.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = ProductAddUpdateSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "successfully updated the product"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDeleteView(generics.DestroyAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [
        IsAuthenticated, (SuperAdminPermission | UberAdminPermission | ProductManagerPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return ProductPanel.objects.get(id=pk)
        except ProductPanel.DoesNotExist:
            raise Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        self.perform_destroy(instance)
        return Response({"message": "product deleted successfully"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------------------------------------
# PRODUCT CATEGORIES
# ---------------------------------------------------------------------------------------------------------

class ProductCategoriesListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):
        name_query = request.query_params.get('name')
        status_query = request.query_params.get('status')
        dropdown = request.query_params.get('dropdown')
        
        product = ProductTier1.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")
        
        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(product, request)

        serializer = ProductCategoriesSerializer(paginated_data, many=True)
        count = product.count()

        response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }
        
        if dropdown is not None:
            serializer = ProductCategoryDropdownSerializer(product, many=True)
            return Response({"data":serializer.data})

        if name_query or status_query:
            if name_query:
                queryset = product.filter(name__icontains=name_query)
            if status_query:
                queryset = product.filter(status=status_query)

            paginated_data = paginator.paginate_queryset(queryset, request)

            serializer = ProductCategoriesSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
                'data': serializer.data,
                'next': paginator.get_next_link(),
                'previous': paginator.get_previous_link(),
                'total': count
                }

            return Response(response_data)

        return Response(response_data)
    

class ProductCategoriesDetailView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return ProductTier1.objects.get(id=pk)
        except ProductTier1.DoesNotExist:
            raise Http404
        
    def get_product(self, pk):
            try:
                return ProductPanel.objects.filter(service=pk, deleted_at__isnull=True)
            except ProductPanel.DoesNotExist:
                return None
    
        
    def get(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = ProductCategoriesDetailSerializer(instance)
        
        productInstance = self.get_product(pk)
        product = ProductSerializer(instance=productInstance, many=True)
        
        response_data = {
            "data": {
                "product_category": serializer.data,
                "related_products": product.data
            }
        }
        return Response(response_data)


class ProductCategoriesCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def post(self, request):
        serializer = ProductCategoriesCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "product category created"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductCategoriesUpdateView(generics.UpdateAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return ProductTier1.objects.get(id=pk)
        except ProductTier1.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = ProductCategoriesUpdateSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "successfully updated"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductCategoriesDeleteView(generics.DestroyAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return ProductTier1.objects.get(id=pk)
        except ProductTier1.DoesNotExist:
            raise Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        self.perform_destroy(instance)
        return Response({"message": "product category deleted successfully"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------------------------------------
# INTERACTIONS CRUD
# ---------------------------------------------------------------------------------------------------------


class InteractionsListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):
        status_query = request.query_params.get('status')
        name_query = request.query_params.get('name')
        dropdown = request.query_params.get('dropdown')

        queryset = CallToActionPro.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")
        

        #PAGINATION
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginated_data = paginator.paginate_queryset(queryset, request)

        serializer = InteractionsSerializer(paginated_data, many=True)
        count = queryset.count()

        response_data = {
            'data': serializer.data,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'total': count
            }

        if dropdown is not None:
            serializer = InteractionsDropdownSerializer(queryset, many=True)
            return Response({"data":serializer.data})

        if status_query or name_query:
            queryset = CallToActionPro.objects.all()
            if status_query:
                queryset = queryset.filter(status__icontains=status_query)
            if name_query:
                queryset = queryset.filter(name__icontains=name_query)

            paginated_data = paginator.paginate_queryset(queryset, request)

            serializer = InteractionsSerializer(paginated_data, many=True)
            count = queryset.count()

            response_data = {
                    'data': serializer.data,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                    'total': count
                }
            return Response(response_data)

        return Response(response_data)
    

class InteractionsDetailView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return CallToActionPro.objects.get(id=pk)
        except CallToActionPro.DoesNotExist:
            raise Http404
        
    def get(self, request, pk):
        instance = self.get_object(pk)
        serializer = InteractionsDetailSerializer(instance)
        return Response({"data":serializer.data})
        

class InteractionsCreateView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission)]

    def post(self, request):
        # body = json.loads(request.body)
        # data = body['data']
        serializer = InteractionsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "successfully created action type"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InteractionsUpdateView(generics.UpdateAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return CallToActionPro.objects.get(id=pk)
        except CallToActionPro.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = InteractionsUpdateSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "successfully updated action type"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InteractionsDeleteView(generics.DestroyAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get_object(self, pk):
        try:
            return CallToActionPro.objects.get(id=pk)
        except CallToActionPro.DoesNotExist:
            raise Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        self.perform_destroy(instance)
        return Response({"message": "Interaction deleted successfully"}, status=status.HTTP_200_OK)

# ---------------------------------------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------------------------------------


class SettingsView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          ( UberAdminPermission | IsAdminUser)]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            settings = SiteConfig.objects.first()
            
            if not settings:
                settings = SiteConfig.objects.create()

            if settings.browse_without_login:
                self.authentication_classes = []
                self.permission_classes = []
            else:
                self.authentication_classes = [JWTAuthentication]
                self.permission_classes = [IsAuthenticated,
                                            (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
        
        return super().get_permissions()

    def get(self, request):
        instance = SiteConfig.objects.first()
        serializer = SettingsSerializer(instance)
        return Response({"data": (serializer.data)})

    def post(self, request):
        instance = SiteConfig.objects.first()
        serializer = SettingsUpdateSerializer(
            instance, data=request.data, partial=True) 

        if serializer.is_valid():
            data = serializer.save()
            try:
                prev_obj = AuditTrail.objects.filter(
                    object_id=instance.id).order_by('-created_at')[0]
            except:
                prev_obj = None
            for each_obj in range(len(list(serializer.initial_data.keys()))):
                store_audit(
                settings_object=(list(serializer.initial_data.keys())[each_obj]).replace('_',' ').upper(),
                request=self.request,
                instance=data,
                action="UPDATE",
                previous_instance=prev_obj
                )
            return Response({
                "message": "successfully updated",
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        instance = SiteConfig.objects.first()
        try:
            fields_to_clear = request.data.get('data')
        except AttributeError:
            return Response({"error":"invalid request payload"}, status=status.HTTP_400_BAD_REQUEST)
        
        if fields_to_clear:
            pass
        else:
            return Response({"error": "incorrect data format"}, status=status.HTTP_400_BAD_REQUEST)
        for field in fields_to_clear:
            if field == 'interactions':
                setattr(instance, 'cta','')
            elif field == 'categories':
                setattr(instance, 'sector', '')
            elif field == 'product_categories':
                setattr(instance,'product_tier_1','')
            elif field == 'product':
                setattr(instance,'product_entities_tier_3','')
            elif hasattr(instance, field):
                setattr(instance, field, '')
            else:
                return Response({'error': f'{field} is not a valid field'}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.save()
        for each_obj in range(len(fields_to_clear)):
            store_audit(
                settings_object=(fields_to_clear[each_obj].replace('_',' ')).upper(),
                request=self.request,
                instance=instance,
                action="DELETE",
                previous_instance=AuditTrail.objects.filter(
                        object_id=instance.id).order_by('-created_at')[0]
            )

        return Response({'message': f'{fields_to_clear} cleared'}, status=status.HTTP_200_OK)


class HomePageSettingsView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (UberAdminPermission | IsAdminUser)]

    def get(self, request):
        instance = HomePageOption.objects.first()
        serializer = HomePageSerializer(instance)
        if (serializer.data['option']=='SCENE'):
            scene = Scene.objects.filter(deleted_at__isnull = True)
            unity_scene = serializer.data['scene']
            related_scene = {}
            for i in scene:
                if i.unity_scene is not None and i.unity_scene.id == unity_scene:
                    related_scene = i
                    response_data = {
                        "data":{
                        "option":serializer.data['option'],
                        "image":serializer.data['image'],
                        "scene":serializer.data['scene'],
                        "video_embed_code":serializer.data['video_embed_code'],
                        "associated_scene":{
                            "id":related_scene.id,
                            "title":related_scene.title,
                            "slug":related_scene.slug,
                            "image":related_scene.image.url
                        }}}
                    return Response(response_data)
            return Response({"data":(serializer.data)})

        return Response({"data": (serializer.data)})

    def post(self, request):
        instance = HomePageOption.objects.first()
        serializer = HomePageUpdateSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            data = serializer.save()
            try:
                prev_obj = AuditTrail.objects.filter(
                    object_id=instance.id).order_by('-created_at')[0]
            except:
                prev_obj = None

            store_audit(
            settings_object=(list(serializer.initial_data.keys())[0]).replace('_',' ').upper(),
            request=self.request,
            instance=data,
            action="UPDATE",
            previous_instance=prev_obj
            )

            return Response({
                "message": "successfully updated",
            })
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ThemeSettingView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (UberAdminPermission | IsAdminUser)]

    def get(self, request):
        instances = ThemeOption.objects.filter(
            deleted_at__isnull=True).order_by()
        data = {instance.key: instance.value for instance in instances}
        return Response({"data": data})

    def post(self, request):
        data = request.data.get('data', {})
        for key, value in data.items():
            if not value:
                try:
                    instance = ThemeOption.objects.get(key=key)
                    instance.delete()

                    try:
                        prev_obj = AuditTrail.objects.filter(model_type='Theme Option',
                        object_id=instance.id).order_by('-created_at')[0]
                    except:
                        prev_obj = None

                    store_audit(
                    request=self.request,
                    instance=instance,
                    action="DELETE",
                    previous_instance=prev_obj
                    )

                except ThemeOption.DoesNotExist:
                    pass
            else:
                obj, created = ThemeOption.objects.get_or_create(key=key)
                obj.deleted_at = None
                obj.value = value
                obj.save()

                try:
                    prev_obj = AuditTrail.objects.filter(model_type = 'Theme Option',
                        object_id=obj.id).order_by('-created_at')[0]
                except:
                    prev_obj = None

                store_audit(
                request=self.request,
                instance=obj,
                action="UPDATE",
                previous_instance=prev_obj
                )

        return Response({"message": f"Successfully created / updated the values for the key",
                         "data": data})


class FilterIconView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):
        instance = FilterIcon.objects.first()
        serializer = FilterIconSerializer(instance)
        return Response({"data":serializer.data})

    def post(self, request):
        instance = FilterIcon.objects.first()
        if not instance:
            instance = FilterIcon.objects.create()
        serializer = FilterIconUpdateSerializer(
            instance, data=request.data, partial=True)
        if serializer.is_valid():
            data = serializer.save()
            try:
                prev_obj = AuditTrail.objects.filter(model_type = 'Filter Icon',
                    object_id=instance.id).order_by('-created_at')[0]
            except:
                prev_obj = None
            for each_obj in range(len(list(serializer.initial_data.keys()))):
                store_audit(
                settings_object=(list(serializer.initial_data.keys())[each_obj]).replace('_',' ').upper(),
                request=self.request,
                instance=data,
                action="UPDATE",
                previous_instance=prev_obj
                )
            return Response({"message": "successfully updated"}, status=status.HTTP_200_OK)
        return Response({"error": (serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)


class FilterActionView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
    
    def get(self, request):
        instance = ActionType.objects.all().order_by("id")
        serializer = FilterActionSerializer(instance, many=True)
        return Response({"data":serializer.data})
    
    def post(self, request):
        body = json.loads(request.body)
        id = body['data']['id']
        for i in id:
            obj = ActionType.objects.get(id=i)
            if obj.show_in_filter == True:
                obj.show_in_filter = False
            else:
                obj.show_in_filter = True
            obj.save()
            try:
                prev_obj = AuditTrail.objects.filter(model_type='Action Type',
                object_id=obj.id).order_by('-created_at')[0]
            except:
                prev_obj = None

            store_audit(
                settings_object=obj.text,
                request=self.request,
                instance=obj,
                action="UPDATE",
                previous_instance=prev_obj
                )

        return Response({"message":"success"}, status=status.HTTP_200_OK)
       


class ShareIconView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (UberAdminPermission | IsAdminUser)]
    
    def get_permissions(self):
        if self.request.method == 'GET':
            settings = SiteConfig.objects.first()
            
            if not settings:
                settings = SiteConfig.objects.create()

            if settings.browse_without_login:
                self.authentication_classes = []
                self.permission_classes = []
            else:
                self.authentication_classes = [JWTAuthentication]
                self.permission_classes = [IsAuthenticated,
                                            (UberAdminPermission | IsAdminUser)]
        
        return super().get_permissions()

    def get(self, request):
        instance = ShareIcon.objects.first()
        serializer = ShareIconSerializer(instance)
        response_data = {
            "data":[
            {
            "id":1,
            "name":"Facebook",
            "value":(serializer.data['show_facebook'])
            },
            {
            "id":2,
            "name":"Twitter",
            "value":(serializer.data['show_twitter'])
            },
            {
            "id":3,
            "name":"Linkedin",
            "value":(serializer.data['show_linkedin'])
            },
            {
            "id":4,
            "name":"Pinterest",
            "value":(serializer.data['show_pinterest'])
            },
            {
            "id":5,
            "name":"Email",
            "value":(serializer.data['show_email'])
            },
            {
            "id":6,
            "name":"Copy Link",
            "value":(serializer.data['show_copy_link'])
            }]
        }
        return Response(response_data)
    
    def post(self, request):
        instance = ShareIcon.objects.first()
        body = json.loads(request.body)
        id = body['data']['id']
        if not instance:
            instance = ShareIcon.objects.create()

        for i in id:
            if i not in [1, 2, 3, 4, 5, 6]:
                return Response({"error": "valid id not supplied"})
            
        try:
            prev_obj = AuditTrail.objects.filter(model_type = 'Share Icon',
                object_id=instance.id).order_by('-created_at')[0]
        except:
            prev_obj = None
            
        for i in id:
            if i == 1:
                instance.show_facebook = not instance.show_facebook
                title = 'FACEBOOK'
            elif i == 2:
                instance.show_twitter = not instance.show_twitter
                title = 'TWITTER'
            elif i == 3:
                instance.show_linkedin = not instance.show_linkedin
                title = 'LINKEDIN'
            elif i == 4:
                instance.show_pinterest = not instance.show_pinterest
                title = 'PINTEREST'
            elif i == 5:
                instance.show_email = not instance.show_email
                title = 'EMAIL'
            elif i == 6:
                instance.show_copy_link = not instance.show_copy_link
                title = 'COPY LINK'
            instance.save()

            store_audit(
            settings_object=title,
            request=self.request,
            instance=instance,
            action="UPDATE",
            previous_instance=prev_obj
            )
            
        return Response({"message": "success"}, status=status.HTTP_200_OK)
    

class SceneGroupView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]

    def get(self, request):
        instance = SceneGroup.objects.filter(
            deleted_at__isnull=True).order_by("-created_at")
        serializer = SceneGroupSerializer(instance, many=True)
        return Response({'data':serializer.data})
    
    def post(self, request):
        data = request.data.get('data', {})
        serializer = SceneGroupSerializer(data=data)
        if serializer.is_valid():
            try:
                data = serializer.save()
                store_audit(
                settings_object=data.name,
                request=self.request,
                instance=data,
                action="CREATE",
                )
            except Exception as e:
                return Response({"name": ["Scene group with that name already exists"]}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "success"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class SceneGroupUpdateView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]
    
    def get_object(self, pk):
        try:
            return SceneGroup.objects.get(id=pk)
        except SceneGroup.DoesNotExist:
            return Http404
        
    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        data = request.data.get('data', {})
        serializer = SceneGroupSerializer(
            instance, data=data, partial=True)
        if serializer.is_valid():
            data = serializer.save()
            try:
                prev_obj = AuditTrail.objects.filter(model_type = 'Scene Group',
                    object_id=instance.id).order_by('-created_at')[0]
            except:
                prev_obj = None

            store_audit(
                request=self.request,
                instance=data,
                action="UPDATE",
                previous_instance=prev_obj
                )
            
            return Response({"message": "success", "data": (serializer.data)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SceneGroupDeleteView(generics.DestroyAPIView, CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser)]   

    def get_object(self, pk):
        try:
            return SceneGroup.objects.get(id=pk)
        except SceneGroup.DoesNotExist:
            return Http404

    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        self.perform_destroy(instance)
        try:
            prev_obj = AuditTrail.objects.filter(model_type = 'Scene Group',
                object_id=instance.id).order_by('-created_at')[0]
        except:
            prev_obj = None

        store_audit(
            request=self.request,
            instance=instance,
            action="DELETE",
            previous_instance=prev_obj
            )
        return Response({"message": "Scene Group deleted successfully"}, status=status.HTTP_200_OK)
    

class ConfigView(CustomAPIView):

    authentication_classes = []
    permission_classes = []

    # def dispatch(self, request, *args, **kwargs):
    #     settings = SiteConfig.objects.first()
    #     if settings.browse_without_login:
    #         self.authentication_classes = []
    #         self.permission_classes = []
    #     else:
    #         self.authentication_classes = [JWTAuthentication]
    #         self.permission_classes = [IsAuthenticated,
    #                                     (SuperAdminPermission | UberAdminPermission)]
    #     return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        instance = HomePageOption.objects.first()
        settings = SiteConfig.objects.first()

        if not instance:
            instance = HomePageOption.objects.create()

        if not settings:
            settings = SiteConfig.objects.create()
        
        isImmersive = settings.immersive_experience
        title = None if settings.title == '' else settings.title    
        favicon = None if settings.favicon == '' else settings.favicon.url
        browse_without_login = settings.browse_without_login

        theme_obj = ThemeOption.objects.filter(deleted_at__isnull=True).order_by()
        theme_settings = {obj.key: obj.value for obj in theme_obj}

        if instance.option == 'IMAGE':
            if instance.image:
                data = {
                    "type": "IMAGE",
                    "image":instance.image.url
                }
            else:
                data = {
                    "type":"IMAGE",
                    "image":None
                }

        elif instance.option == 'VIDEO':
            if instance.video_embed_code:
                data = {
                    "type":"VIDEO",
                    "video_embed_code":instance.video_embed_code
                }
            else:
                data = {
                    "type":"VIDEO",
                    "video_embed_code":"null"
                }
        else:
            serializer = UnitySceneSerializer(instance.scene)
            
            try:
                associated_scene = Scene.objects.get(unity_scene = instance.scene)
            except Scene.DoesNotExist:
                associated_scene = None
            
            data = { 
                "type":"SCENE",
                'unity_scene_id':serializer.data['id'],
                'name':serializer.data['name'],
                'background_image':serializer.data['background_image'],
                'loading_text':serializer.data['loading_text'],
            }
            
            if associated_scene:
                associated_scene_data = SceneSerializer(associated_scene)
                data['associated_scene'] = {
                    'id' : associated_scene_data.data['id'],
                    'title' : associated_scene_data.data['title'],
                    'slug': associated_scene_data.data['slug'],
                    'image': associated_scene_data.data['image']
                }

            
        if isImmersive:
            immersive_experience = True
            scene = SiteConfig.objects.first().default_scene
            serializer = SceneSerializer(scene)
            
           
            obj = Scene.objects.get(id=scene.id)
            try:
                unity_scene = UnityScene.objects.get(id=obj.unity_scene.id)
                loading_text = unity_scene.loading_text
            except:
                loading_text = settings.default_loading_text       

            if settings.loading_image:
                loading_image = settings.loading_image.url
            else:
                loading_image = None


            data = {
                "scene_id":serializer.data["id"],
                "scene_title":serializer.data["title"],
                "background_image":serializer.data["image"],
                "loading_text":loading_text,
                "loading_image":loading_image
            }

            response_key = 'immersive_details'

        else:
            immersive_experience = False
            response_key = 'homepage'

        response_data = {
            "title":title,
            "favicon":favicon,
            "immersive_experience":immersive_experience,
            "browse_without_login":browse_without_login,
            response_key : data,
            "theme_settings":theme_settings
        }

        return Response({"data":response_data})
    
# ---------------------------------------------------------------------------------------------------------
# FILE LIBRARY
# ---------------------------------------------------------------------------------------------------------

class FileLibraryView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated,
                          (SuperAdminPermission | UberAdminPermission | IsAdminUser | ExperienceDesignerPermission | ProductManagerPermission)] 
    
    def get_main_folder(self):
        try:
            return FileLibrary.objects.get(parent=None)
        except FileLibrary.DoesNotExist:
            return FileLibrary.objects.create(name='File Library', parent=None)

        
    def get(self, request, pk=None):
        if pk:
            return Response({'error':['Method not allowed']}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        main_folder = self.get_main_folder()
        # folders = FileLibrary.objects.filter(parent=None).prefetch_related("sub_folders", "model3Ds")
        folders = FileLibrary.objects.filter(parent=None).prefetch_related(
    Prefetch("model3Ds", queryset=Model3D.objects.filter(deleted_at__isnull=True)))

        folders_data = []
        for folder in folders:
            folder_data = {
                "id": folder.id,
                "name": folder.name,
                "model_3Ds": [],
                "sub_folders": []
            }
            for model3d in folder.model3Ds.all():
                try:
                    model3d_data = {
                        "id": model3d.id,
                        "file": model3d.file.url
                    }
                except:
                    model3d_data = {
                        "id": model3d.id,
                        "file": 'none'
                    }
                folder_data["model_3Ds"].append(model3d_data)
            for sub_folder in folder.sub_folders.all():
                sub_folder_data = {
                    "id": sub_folder.id,
                    "name": sub_folder.name,
                }

                #--------------------------------------------------------
                # sub_folder_data["model_3Ds"] = []
                # for model3d in sub_folder.model3Ds.all():
                #     model3d_data = {
                #         "id": model3d.id,
                #         "file": model3d.file.url
                #     }
                #     sub_folder_data["model_3Ds"].append(model3d_data)
                #--------------------------------------------------------


                folder_data["sub_folders"].append(sub_folder_data)
            
            folders_data.append(folder_data)

        return Response({"data":folders_data[0]})

    def get_parent_folder(self, pk):
        try:
            return FileLibrary.objects.get(pk=pk)
        except FileLibrary.DoesNotExist:
            raise Http404

    def post(self, request, pk=None):
        data = request.data.copy()
        main_folder = self.get_main_folder()
        if pk:
            parent_folder = self.get_parent_folder(pk)
        else:
            parent_folder = main_folder
        data["parent"] = parent_folder.pk
        serializer = FileLibrarySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        folder = serializer.save()

        def set_parent(folder, parent):
            folder.parent = parent
            folder.save()
            for subfolder in folder.sub_folders.all():
                set_parent(subfolder, folder)

        set_parent(folder, parent_folder)

        return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)


class FileLibraryFolderDetailView(generics.RetrieveAPIView, CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = FileLibrary.objects.all()
    serializer_class = Model3DSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        folders = FileLibrary.objects.filter(parent=obj).prefetch_related("sub_folders", "model3Ds")
        model3D = Model3D.objects.filter(folder=obj, deleted_at__isnull = True)
        folders_data = []
        model_3Ds = []
        response_data = {
            "id":obj.id,
            "name":str(obj),
            "model_3Ds":model_3Ds,
            "sub_folders":folders_data,
        }
        for item in model3D:
            folder_data = {
                "id": item.id,
                "file": item.file.name,
            }
            model_3Ds.append(folder_data)
        for folder in folders:
            folder_data = {
                "id": folder.id,
                "name": folder.name,
            }
            folders_data.append(folder_data)

        return Response({"data":response_data})
    

class FileLibraryUpdateView(generics.UpdateAPIView, CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return FileLibrary.objects.get(id=pk)
        except FileLibrary.DoesNotExist:
            raise Http404

    def put(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        serializer = FileLibraryUpdateSerializer(
            instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "success", "data": (serializer.data)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Model3DCreateView(CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return FileLibrary.objects.get(id=pk)
        except FileLibrary.DoesNotExist:
            raise Http404
    
    def post(self, request, pk):
        folder = get_object_or_404(FileLibrary, pk=pk)
        model3D = Model3D(folder=folder)
        serializer = Model3DSerializer(model3D, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"model 3D created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class Model3DDeleteView(generics.DestroyAPIView, CustomAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return Model3D.objects.get(id=pk, deleted_at__isnull = True)
        except Model3D.DoesNotExist:
            raise Http404
        
    def destroy(self, request, pk, *args, **kwargs):
        instance = self.get_object(pk)
        self.perform_destroy(instance)
        return Response({"message": "model 3D deleted successfully"}, status=status.HTTP_200_OK)
    

class Model3DListView(CustomAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        model3d = Model3D.objects.filter(deleted_at__isnull = True).order_by("-created_at")
        serializer = Model3DSerializer(model3d, many=True)
        return Response({"data":serializer.data})


# ---------------------------------------------------------------------------------------------------------
# JSON WEB TOKEN
# ---------------------------------------------------------------------------------------------------------

class GetAccessTokenView(TokenRefreshView):

    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data['data']
        try:
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                new_access_token = serializer.validated_data['access']
                new_refresh_token = serializer.validated_data['refresh']

                # Generates a new refresh token with access token > so settings.py BLACKLIST_AFTER_ROATATION = True

                return Response({"data": {
                    'refresh_token': str(new_refresh_token),
                    'access_token': str(new_access_token)

                }
                }, status=status.HTTP_200_OK)
                
        except TokenError as e:
            if 'blacklisted' in str(e):
                return Response({"error": "Token has been blacklisted"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Token is invalid or expired"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "error", "response": (serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
