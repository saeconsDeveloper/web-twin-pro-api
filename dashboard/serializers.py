import os
import time
from django.utils.text import slugify

from django.contrib.auth.models import Group
from django.core.validators import EmailValidator
from PIL import Image
from rest_framework import serializers

from .models import (CallToActionPro, FilterIcon, HomePageOption, ProductPanel,
                     ProductTier1, Scene, Sector, SiteConfig, UnityScene, User, FileLibrary, Model3D, AuditTrail, ActionType, ShareIcon, SceneGroup, UnitySceneVersion)
from .services import get_random_position
from .utils import reset_user_password, extract_unity_file
from django.db import transaction
from django.core.exceptions import ValidationError



#--------------------------------------------------------------------------------
# USER SERIALIZERS
#--------------------------------------------------------------------------------
class GroupSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='name')
    class Meta:
        model = Group
        fields = [
            'id', 
            'role'
            ]


class UserSerializer(serializers.ModelSerializer):

    # groups = serializers.StringRelatedField(many=True)
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'date_joined',
            'groups',
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)
    email = serializers.EmailField(
        required=True,
        validators=[EmailValidator(message="Invalid email format")])

    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'email',
            'role',
            ]
        
    def validate_role(self, role):
        if Group.objects.filter(name=role).exists():
            return role
        raise serializers.ValidationError("role is invalid or doesn't exist")

    def validate_email(self, email):
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError("this email address is already in use.")
        return email
    
    def create(self, validated_data):
        role = validated_data.pop("role", None)
        email = validated_data.get("email", None)
        user = super().create(validated_data)
        group = Group.objects.get(name=role)
        user.username = email
        user.groups.add(group)
        reset_user_password(user=user)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True)
    # user_email = serializers.CharField(write_only=True)
    groups = GroupSerializer(many=True)
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'groups',
            'role',
            'email',
    
        ]
    # username = serializers.CharField(read_only=True)
    def validate_role(self, role):
        if Group.objects.filter(name=role).exists():
            return role
        raise serializers.ValidationError("role is invalid or doesn't exist")

    def validate_email(self, email):
        instance = self.instance
        if (instance.username == email):
            pass
        elif User.objects.filter(username=email).exists():
            raise serializers.ValidationError("this email is already in use")
        return email

    def update(self, instance, validated_data):
        user = User.objects.get(username=instance)
        f_name = validated_data.get('first_name')
        l_name = validated_data.get('last_name')
        role = validated_data.get('role')
        email = validated_data.get('email')
        if role:
            group = Group.objects.get(name=role)
            user.groups.clear()
            user.groups.add(group.id)
        if email:
            user.email = email
            user.username = email
        if f_name:
            user.first_name = f_name
        if l_name:
            user.last_name = l_name
        user.save()
        return user

#--------------------------------------------------------------------------------
# AUDIT SERIALIZERS
#--------------------------------------------------------------------------------

class AuditTrailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = AuditTrail
        fields = [
            "id",
            "user",
            "model_type",
            # "object_id",
            "object_str",
            "action",
            "ip",
            # "instance",
            # "previous_instance",
            "created_at",
            "updated_at",
        ]

#--------------------------------------------------------------------------------
# SCENES CATEGORIES SERIALIZERS
#--------------------------------------------------------------------------------

class SceneCategoriesDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = [
            'id',
            'name',
            'status'
        ]


class SceneCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "category_id",
            "status",
            "image",
            "description",
            "banner_image",
            "slug",
            "show_in_filter",
            "position_x",
            "position_y"
        ]

    def update(self, instance, validated_data):
        instance = self.instance
        image = validated_data.pop('image', None)

        if image:
            instance.image = image
        elif image == '':
            instance.image = None
        return super().update(instance, validated_data)


class SceneCategoriesCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = [
            'name',
            'category_id',
            'image',
            'description',
            'banner_image',
            'status',
        ]
        def validate_image(self, image):
            try:
                img = Image.open(image)
            except Exception as e:
                raise serializers.ValidationError({"error":"not a valid image file"})

            if img.format.lower() not in ['jpeg', 'png', 'svg', 'jpg']:
                raise serializers.ValidationError({"error":"image file format not supported only ( jpeg, jpg, svg, png ) allowed"})
            return image
            
        def validate_banner_image(self, banner_image):
            try:
                img = Image.open(banner_image)
            except Exception as e:
                raise serializers.ValidationError({"error":"not a valid image file"})

            if img.format.lower() not in ['png']:
                raise serializers.ValidationError({"error":"image file format not supported only ( png ) allowed"})
            return banner_image


class SceneCategoriesFilterSerializer(serializers.ModelSerializer):
    value = serializers.BooleanField(source='show_in_filter')
    class Meta:
        model = Sector
        fields = [
            "id",
            "name",
            "value"
        ]
            
            
#--------------------------------------------------------------------------------
# UNITY SCENES SERIALIZERS 
#--------------------------------------------------------------------------------

class UnitySceneDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnityScene
        fields = [
            'id',
            'name'
        ]

class UnitySceneSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnityScene
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "background_image",
            "loading_text",
            "unity_file",
        ]

    def update(self, instance, validated_data):
        instance = self.instance
        background_image = validated_data.get('background_image', None)
        if background_image:
            instance.background_image = background_image
        elif background_image == '':
            instance.background_image = None
        return super().update(instance, validated_data)

class UnitySceneCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnityScene
        fields = ["name", "unity_file", "background_image", "loading_text"]

    def create(self, validated_data):
        data = super().create(validated_data)
        extract_unity_file(data)
        return data
    
#--------------------------------------------------------------------------------
# UNITY SCENES VERSIONS
#--------------------------------------------------------------------------------

class UnitySceneVersionSerializer(serializers.ModelSerializer):
    version_name = serializers.CharField(source='version')
    class Meta:
        model = UnitySceneVersion
        fields = [
            # 'unity_scene',
            'id',
            'version_name',
            'content_json'
        ]

    def update(self, instance, validated_data):
        instance = self.instance
        version_name = validated_data.get('version_name')
        content_json = validated_data.get('content_json')
        print(content_json)
        if version_name:
            instance.version = version_name
        if content_json:
            instance.content_json = content_json
        return super().update(instance, validated_data)

class UnitySceneVersionCreateSerializer(serializers.ModelSerializer):
    version_name = serializers.CharField(source='version', write_only=True)
    class Meta:
        model = UnitySceneVersion
        fields = [
            'unity_scene',
            'version_name',
            # 'content_json'
        ]

#--------------------------------------------------------------------------------
# PRODUCT
#--------------------------------------------------------------------------------

class ProductDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPanel
        fields = [
            'id',
            'display_text',
            'status'
        ]
    

class ProductSerializer(serializers.ModelSerializer):
    product_category = serializers.StringRelatedField(source='service')
    hyper_link = serializers.CharField(source='hyperlink')
    name = serializers.CharField(source='display_text')
    description = serializers.CharField(source='product_description')
    price = serializers.IntegerField(source='pricing_of_tiers')
    manager_name = serializers.CharField(source='service_owner')
    vendor_service_name = serializers.CharField(source='asset')
    vendor_service_desc = serializers.CharField(source='asset_description')
    class Meta:
        model = ProductPanel
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "hyper_link",
            "description",
            "model_3d",
            "price",
            "vendor",
            'vendor_service_name',
            'vendor_service_desc',
            "priority",
            "manager_name",
            "how_to_request",
            "position_x",
            "position_y",
            "slug",
            "status",
            "product_category",
            "subcategory"
        ]

class ProductCategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTier1
        fields = [
            'id',
            'name'
        ]

class ProductDetailSerializer(serializers.ModelSerializer):
    product_category = ProductCategoryDetailSerializer(source='service')
    hyper_link = serializers.CharField(source='hyperlink')
    name = serializers.CharField(source='display_text')
    description = serializers.CharField(source='product_description')
    price = serializers.IntegerField(source='pricing_of_tiers')
    manager_name = serializers.CharField(source='service_owner')
    vendor_service_name = serializers.CharField(source='asset')
    vendor_service_desc = serializers.CharField(source='asset_description')
    class Meta:
        model = ProductPanel
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "hyper_link",
            "description",
            "model_3d",
            "price",
            "vendor",
            'vendor_service_name',
            'vendor_service_desc',
            "priority",
            "manager_name",
            "how_to_request",
            "position_x",
            "position_y",
            "slug",
            "status",
            "product_category",
            "subcategory"
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        model_3d_path = data.get('model_3d')
        if model_3d_path:
            path = model_3d_path.replace('/media/','')
            try:
                model_3d = Model3D.objects.get(file__exact=path)
                serializer = ProductCategoryModel3DSerializer(model_3d)
                data['model_3d'] = serializer.data
            except Model3D.DoesNotExist:
                data['model_3d'] = None
        return data

class ProductAddUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='display_text')
    description = serializers.CharField(source='product_description')
    vendor_service_name = serializers.CharField(source='asset', required=False)
    vendor_service_desc = serializers.CharField(source='asset_description', required=False)
    price = serializers.IntegerField(source='pricing_of_tiers', required=False)
    manager_name = serializers.CharField(source='service_owner', required=False)
    hyper_link = serializers.CharField(source='hyperlink', required=False)
    product_category = serializers.PrimaryKeyRelatedField(
        queryset=ProductTier1.objects.all(), source='service'
    )
    model_3d = serializers.CharField(allow_blank=True)
    class Meta:
        model = ProductPanel
        fields = [
            'product_category',
            'name',
            'hyper_link',
            'description',
            'vendor_service_name',
            'vendor_service_desc',
            'price',
            'vendor',
            'manager_name',
            'how_to_request',
            'status',
            'model_3d'
        ]
    
    def create(self, validated_data):
        model_3d = validated_data.pop('model_3d', None)
        if model_3d:
            obj = Model3D.objects.get(id=model_3d)
            file = obj.file
            validated_data['model_3d'] = file
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        instance = self.instance
        model_3d = validated_data.get('model_3d')
        if model_3d:
            instance.model_3d = None
            obj = Model3D.objects.get(id=model_3d)
            file = obj.file
            validated_data['model_3d'] = file
        elif model_3d == '':
            validated_data['model_3d'] = None
        return super().update(instance, validated_data)
    
    def validate_model_3d(self, model_3d):
        if not model_3d:
            return model_3d
        
        if Model3D.objects.filter(id=model_3d, deleted_at__isnull=True).exists():
            return model_3d
        raise serializers.ValidationError('model_3d is deleted or doesnt exists')
    

    def save_with_position(self):
        data = self.validated_data
        if data.get('position_x') and data.get('position_y'):
            return

        position_x, position_y = get_random_position()
        timeout = time.time() + 5  # 5 seconds to wait for while loop
        try:
            while ProductPanel.objects.filter(
                position_x__gt=position_x - 1,
                position_x__lt=position_x + 1,
                position_y__gt=position_y - 1,
                position_y__lt=position_y + 1,
            ).exists():
                position_x, position_y = get_random_position()
                if time.time() > timeout:
                    # if no position is found in 5 seconds then raise exception
                    # to get random (possibly overlapping) position
                    raise Exception()
        except Exception:
            position_x, position_y = get_random_position()

        data['position_x'] = position_x
        data['position_y'] = position_y
        self.save()
        

#--------------------------------------------------------------------------------
# PRODUCTS CATEGORIES
#--------------------------------------------------------------------------------

class ProductCategoryDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTier1
        fields = [
            'id',
            'name',
            'status'
        ]


class ProductCategoriesSerializer(serializers.ModelSerializer):
    related_products = serializers.SerializerMethodField()
    class Meta:
        model = ProductTier1
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "status",
            "image",
            "description",
            "model_3d",
            "product_button_id",
            "icon_image",
            "show_in_filter",
            "position_x",
            "position_y",
            "sector",
            "related_products"
        ]

    def get_related_products(self, obj):
        related_products = ProductPanel.objects.filter(service=obj.id, deleted_at__isnull=True)
        serializer = ProductSerializer(related_products, many=True)
        if serializer.data:
            return serializer.data
        return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            model_3d_type = 'fbx' if data["model_3d"].split(".")[-1] == 'fbx' else 'gltf'
        except:
            model_3d_type = None
        data['model_3d_type'] = model_3d_type
        return data


class ProductCategoriesCreateSerializer(serializers.ModelSerializer):
    model_3d = serializers.CharField(write_only=True, required=False)
    icon_image = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = ProductTier1
        fields = [
            'name',
            'image',
            'model_3d',
            'product_button_id',
            'description',
            'icon_image',
            'status',
        ]

    def create(self, validated_data):
        model_3d = validated_data.pop('model_3d', None)
        if model_3d:
            obj = Model3D.objects.get(id=model_3d)
            file = obj.file
            validated_data['model_3d'] = file
        return super().create(validated_data)


    def validate(self, data):
        if not data.get('image') and not data.get('model_3d'):
            raise serializers.ValidationError({"error":"field 'image' or 'model_3d' is required"})
        if data.get('image') and data.get('model_3d'):
            raise serializers.ValidationError({"error":"cannot upload both 'image' and 'model_3d', only one allowed"})
        return data
    

    def validate_model_3d(self, value):
        if Model3D.objects.filter(id=value, deleted_at__isnull=True).exists():
            return value
        raise serializers.ValidationError({'error':'model_3d is deleted or doesnt exists'})
       

    def validate_image(self, image):
        if not image:
            return image

        ext = os.path.splitext(image.name)[1].lower()

        if not ext in ['.jpeg', '.png', '.svg', '.jpg']:
            raise serializers.ValidationError('image file format not supported only ( jpeg, jpg, svg, png ) allowed')

        try:
            with Image.open(image) as img:
                img.verify()
        except Exception:
            raise serializers.ValidationError('file is not a valid image.')
        return image
    

    def validate_icon_image(self, icon_image):
        ext = os.path.splitext(icon_image.name)[1].lower()
        if not ext == '.png':
            raise serializers.ValidationError('Icon file must be a PNG image.')
        try:
            with Image.open(icon_image) as icon:
                if icon.format.lower() != 'png':
                    raise serializers.ValidationError('Icon file must be a PNG image.')
                icon.verify()
        except Exception:
            raise serializers.ValidationError('File is not a valid PNG image.')
        return icon_image
    

class ProductCategoriesUpdateSerializer(serializers.ModelSerializer):
    model_3d = serializers.CharField(required=False, allow_blank = True)
    icon_image = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = ProductTier1
        fields = [
            'name',
            'image',
            'model_3d',
            'product_button_id',
            'description',
            'icon_image',
            'status',
        ]

    def update(self, instance, validated_data):
        instance = ProductTier1.objects.get(id=instance.id)
        model_3d = validated_data.pop('model_3d', None)
        image = validated_data.get('image', None)
        
        if image == '':
            instance.image = None
        elif image:
            instance.image = image

        if model_3d == '':
            instance.model_3d = None
        elif model_3d:
            obj = Model3D.objects.get(id=model_3d)
            file = obj.file
            validated_data['model_3d'] = file
        return super().update(instance, validated_data)

    def validate(self, data):
        if data.get('image') and data.get('model_3d'):
            raise serializers.ValidationError({"error":"cannot upload both 'image' and 'model_3d', only one allowed"})
        return data
    
    def validate_model_3d(self, value):
        if not value:
            return value
        
        if Model3D.objects.filter(id=value, deleted_at__isnull=True).exists():
            return value
        raise serializers.ValidationError({'error':'model_3d is deleted or doesnt exists'})
       
    def validate_image(self, image):
        if not image:
            return image

        ext = os.path.splitext(image.name)[1].lower()

        if not ext in ['.jpeg', '.png', '.svg', '.jpg']:
            raise serializers.ValidationError('image file format not supported only ( jpeg, jpg, svg, png ) allowed')

        try:
            with Image.open(image) as img:
                img.verify()
        except Exception:
            raise serializers.ValidationError('file is not a valid image.')

        return image
    
    def validate_icon_image(self, icon_image):
        ext = os.path.splitext(icon_image.name)[1].lower()
        if not ext == '.png':
            raise serializers.ValidationError('Icon file must be a PNG image.')
        try:
            with Image.open(icon_image) as icon:
                if icon.format.lower() != 'png':
                    raise serializers.ValidationError('Icon file must be a PNG image.')
                icon.verify()
        except Exception:
            raise serializers.ValidationError('File is not a valid PNG image.')
        return icon_image


class ProductCategoryModel3DSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='file')
    class Meta:
        model = Model3D
        fields = [
            'id',
            'url',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        model_3d_path = data.get('url')
        path = '/media/' + model_3d_path
        data['url'] = path
        return data


class ProductCategoriesDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductTier1
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "status",
            "image",
            "description",
            "model_3d",
            "product_button_id",
            "icon_image",
            "show_in_filter",
            "position_x",
            "position_y",
            "sector"
        ]
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        model_3d_path = data.get('model_3d')
        if model_3d_path:
            path = model_3d_path.replace('/media/','')
            try:
                model_3d = Model3D.objects.get(file__exact=path)
                serializer = ProductCategoryModel3DSerializer(model_3d)
                data['model_3d'] = serializer.data
            except Model3D.DoesNotExist:
                data['model_3d'] = None
        return data
              

#--------------------------------------------------------------------------------
# INTERACTIONS SERIALIZER
#--------------------------------------------------------------------------------

class InteractionsDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallToActionPro
        fields = [
            'id',
            'name',
            'status'
        ]

class InteractionsSerializer(serializers.ModelSerializer):
    action_type = serializers.StringRelatedField()
    
    class Meta:
        model = CallToActionPro
        fields = [
            "id",
            "action_type",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "unity_scene_annotation_id",
            "annotation_title",
            "unity_scene_teleportation_id",
            "unity_scene_video_id",
            "revenue_stack_number",
            "embed_link",
            "wtp_scene_id",
            "wtp_scene_name",
            "image",
            "status",
            "top",
            "left",
            "scene"
        ]

class InterAction_ActionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='text')
    class Meta:
        model = ActionType
        fields = [
            "id",
            "name"
        ]  

class InteractionsDetailSerializer(serializers.ModelSerializer):

    action_type = InterAction_ActionSerializer()

    class Meta:
        model = CallToActionPro
        fields = [
            "id",
            "action_type",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "name",
            "unity_scene_annotation_id",
            "annotation_title",
            "unity_scene_teleportation_id",
            "unity_scene_video_id",
            "revenue_stack_number",
            "embed_link",
            "wtp_scene_id",
            "wtp_scene_name",
            "image",
            "status",
            "top",
            "left",
            "scene"
        ]

class InteractionsCreateSerializer(serializers.ModelSerializer):
    action_type = serializers.CharField(write_only=True)
    class Meta:
        model = CallToActionPro
        fields = [
            "id",
            "action_type",
            "name",
            "unity_scene_annotation_id",
            "annotation_title",
            "unity_scene_teleportation_id",
            "unity_scene_video_id",
            "revenue_stack_number",
            "embed_link",
            "wtp_scene_id",
            "wtp_scene_name",
            "image",
            "status",
            "top",
            "left",
            "scene"
        ]

    def validate_action_type(self, action_type):
        try:
            return ActionType.objects.get(id=action_type)
        except Exception as e:
            raise serializers.ValidationError({str(e)})

    
class InteractionsUpdateSerializer(serializers.ModelSerializer):
    action_type = serializers.CharField(write_only=True)
    class Meta:
        model = CallToActionPro
        fields = [
            "id",
            "action_type",
            "name",
            "unity_scene_annotation_id",
            "annotation_title",
            "unity_scene_teleportation_id",
            "unity_scene_video_id",
            "revenue_stack_number",
            "embed_link",
            "wtp_scene_id",
            "wtp_scene_name",
            "image",
            "status",
            "top",
            "left",
            "scene"
        ]

    def validate_action_type(self, action_type):
        try:
            return ActionType.objects.get(id=action_type)
        except Exception as e:
            raise serializers.ValidationError({str(e)})
    
    def update(self, instance, validated_data):
        instance = CallToActionPro.objects.get(id=instance.id)
        return super().update(instance, validated_data)

#--------------------------------------------------------------------------------
# SCENES SERIALIZERS
#--------------------------------------------------------------------------------
class SceneDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scene
        fields = [
            'id',
            'title',
            'status'
        ]
    

class SceneSerializer(serializers.ModelSerializer):
    Unity_Scene = serializers.StringRelatedField(source='unity_scene')
    # product_categories = serializers.StringRelatedField(source='tech_and_digital_services_tier_1', many=True)
    # interactions = serializers.StringRelatedField(source='call_to_actions', many=True)
    # scene_categories = serializers.StringRelatedField(source='sectors_and_departments', many=True)
    class Meta:
        model = Scene
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "title",
            "slug",
            "subtitle",
            "status",
            "web_url",
            "image",
            "description",
            "Unity_Scene",
            # "product_categories",
            # "interactions",
            # 'scene_categories',
            "priority",
            # "previous",
            # "next",
            # "legend",
            # "build_your_experience",
            # "parent",
            # "meta_panel_links",
            # "meta_panel_images",
            # "geography",
            "scene_group",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        scene_group_id = data.get('scene_group')
        data.pop('scene_group')
        if scene_group_id:
            sceneGroup = SceneGroup.objects.get(id=scene_group_id)
            serializer = SceneGroupSerializer(sceneGroup)
            data['scene_group'] = serializer.data
        else:
            data['scene_group'] = None
        return data

    
class SceneCategorySerializer(serializers.ModelSerializer):
    Unity_Scene = serializers.StringRelatedField(source='unity_scene')
    class Meta:
        model = Scene
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "status",
            "web_url",
            "image",
            "description",
            "Unity_Scene",
            "priority",
            "scene_group",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        scene_group_id = data.pop('scene_group')
        priority = data.get('priority')

        if scene_group_id:
            sceneGroup = SceneGroup.objects.get(id=scene_group_id)
            serializer = SceneGroupSerializer(sceneGroup)
            data['scene_group'] = {
                'id':serializer.data['id'],
                'name':serializer.data['name'],
                'color':serializer.data['color'],
                'priority':priority
            }
        else:
            data['scene_group'] = None
        return data


class SceneSerializerImmersiveON(serializers.ModelSerializer):
    Unity_Scene = serializers.StringRelatedField(source='unity_scene')
    immersive_default_scene = serializers.BooleanField(write_only=True)

    class Meta:
        model = Scene
        fields = [
            "id",
            "title",
            "slug",
            "subtitle",
            "status",
            "web_url",
            "image",
            "description",
            "Unity_Scene",
            "scene_group",
            "immersive_default_scene"
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        settings = SiteConfig.objects.first()
        scene_group_id = data.get('scene_group')
        data.pop('scene_group')

        if scene_group_id:
            sceneGroup = SceneGroup.objects.get(id=scene_group_id)
            serializer = SceneGroupSerializer(sceneGroup)
            data['scene_group'] = serializer.data
        else:
            data['scene_group'] = None

        if not settings:
            settings = SiteConfig.objects.create()

        scene_id = settings.default_scene.id
        id = data.get('id')
        if scene_id == id:
            data['immersive_default_scene'] = True
        else:
            data['immersive_default_scene'] = False

        return data

class SceneDetailSerializer(serializers.ModelSerializer):
    Unity_Scene = UnitySceneSerializer(source='unity_scene')
    product_categories = ProductCategoriesSerializer(source='tech_and_digital_services_tier_1', many=True)
    interactions = InteractionsSerializer(source='call_to_actions', many=True)
    scene_categories = SceneCategoriesSerializer(source='sectors_and_departments', many=True)
    class Meta:
        model = Scene
        fields = [
            "id",
            # "created_at",
            # "updated_at",
            # "deleted_at",
            "title",
            "slug",
            "subtitle",
            "status",
            "web_url",
            "image",
            "description",
            "Unity_Scene",
            "unity_scene_version",
            "interactions",
            "product_categories",
            'scene_categories',
            "priority",
            "previous",
            "next",
            "legend",
            "build_your_experience",
            "parent",
            "meta_panel_links",
            "meta_panel_images",
            "geography",
            "scene_group",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        settings = SiteConfig.objects.first()
        
        unity_scene_version = data.get('unity_scene_version')

        if unity_scene_version:
            obj = UnitySceneVersion.objects.get(id=unity_scene_version)
            serializer = UnitySceneVersionSerializer(obj)
            data['unity_scene_version'] = serializer.data
        
        if not settings:
            settings = SiteConfig.objects.create()
        
        if settings.immersive_experience:
            data.pop('scene_group')

        return data


class SceneCreateSerializer(serializers.ModelSerializer):
    product_categories = serializers.CharField(write_only=True, required=False)
    interactions = serializers.CharField(write_only=True, required=False)
    scene_categories = serializers.CharField(write_only=True, required=False)
    unity_scene = serializers.IntegerField(write_only = True, required=False)
    scene_group = serializers.IntegerField(write_only = True, required=False)
    # web_url = serializers.URLField()

    class Meta:
        model = Scene
        fields = [
            'title',
            'slug',
            'image',
            'unity_scene',
            'web_url',
            'description',
            'interactions',
            'product_categories',
            'scene_categories',
            'scene_group',
            'status',
            'priority',
        ]

    def create(self, validated_data):
        settings = SiteConfig.objects.first()
    
        if not settings:
            settings = SiteConfig.objects.create()

        interactions = validated_data.pop('interactions',None)
        product_categories = validated_data.pop('product_categories',None)
        scene_categories = validated_data.pop('scene_categories',None)
        scene_group = validated_data.pop('scene_group', None)
       
        with transaction.atomic():
            scene = Scene.objects.create(**validated_data)

            if scene_group:
                if settings.immersive_experience:
                    raise serializers.ValidationError({"scene_group":[
                            "cannot assign scene_group when immersive experience is ON"
                            ]})
                else:
                    try:
                        obj = SceneGroup.objects.get(id=scene_group)
                    except SceneGroup.DoesNotExist:
                        raise serializers.ValidationError({"scene_group":[
                            "scene_group doesn't exist"
                            ]})
                    scene.scene_group = obj
                    scene.save()
                
            if interactions:
                interactions = interactions.split(",")
                for i in interactions:
                    try:
                        obj = CallToActionPro.objects.get(id=i)
                    except CallToActionPro.DoesNotExist:
                        raise serializers.ValidationError({"interactions":[
                            "interactions doesn't exist"
                            ]})
                    except:
                        raise serializers.ValidationError({"interactions":[
                            f"interactions expected an integer but got '{i}'"
                            ]})
                    scene.call_to_actions.add(obj)
            
            if product_categories:
                product_categories = product_categories.split(",")
                for i in product_categories:
                    try:
                        obj = ProductTier1.objects.get(id=i)
                    except ProductTier1.DoesNotExist:
                        raise serializers.ValidationError({"product_categories":[
                            "product_categories doesn't exist"
                            ]})
                    except:
                        raise serializers.ValidationError({"product_categories":[
                            f"product_categories expected an integer but got '{i}'"
                            ]})
                    scene.tech_and_digital_services_tier_1.add(obj)
            
            if scene_categories:
                scene_categories = scene_categories.split(",")
                for i in scene_categories:
                    try:
                        obj = Sector.objects.get(id=i)
                    except Sector.DoesNotExist:
                        raise serializers.ValidationError({"scene_categories":[
                            "scene_categories doesn't exist"
                            ]})
                    except:
                        raise serializers.ValidationError({"scene_categories":[
                            f"scene_categories expected an integer but got '{i}'"
                            ]})
                    scene.sectors_and_departments.add(obj)
        
        return scene
    
    def validate_unity_scene(self, unity_scene):
        try:
            unityScene = UnityScene.objects.get(id=unity_scene)
        except:
            raise serializers.ValidationError("unity scene with this id was not found")
        
        if unityScene.deleted_at is None:
            scene = Scene.objects.filter(deleted_at__isnull=True)
            for i in scene:
                if i.unity_scene == unityScene:
                        raise serializers.ValidationError("unity_scene with this id is already associated with a scene")
            return unityScene
        else:
            raise serializers.ValidationError("cannot select a unity scene that is deleted")
            
    def validate_image(self, image):
        try:
            img = Image.open(image)
        except Exception as e:
            raise serializers.ValidationError("not a valid image file")

        if img.format.lower() not in ['jpeg', 'png', 'svg', 'jpg']:
            raise serializers.ValidationError("image file format not supported only ( jpeg, jpg, svg, png ) allowed")
        return image


class SceneUpdateSerializer(serializers.ModelSerializer):
    product_categories = serializers.CharField(write_only=True, required=False, allow_blank = True)
    interactions = serializers.CharField(write_only=True, required=False, allow_blank = True)
    scene_categories = serializers.CharField(write_only=True, required=False, allow_blank = True)
    unity_scene = serializers.IntegerField(write_only = True, required = False, allow_null=True)
    scene_group = serializers.CharField(write_only = True, required=False, allow_blank=True)
    unity_scene_version = serializers.IntegerField(write_only = True, required=False, allow_null=True)

    class Meta:
        model = Scene
        fields = [
            'title',
            'slug',
            'image',
            'unity_scene',
            'unity_scene_version',
            'web_url',
            'description',
            'interactions',
            'product_categories',
            'scene_categories',
            'scene_group',
            'status',
            'priority',
        ]

    def update(self, instance, validated_data):
        settings = SiteConfig.objects.first()
        
        if not settings:
            settings = SiteConfig.objects.create()

        scene = instance
        interactions = validated_data.pop('interactions', None)
        product_categories = validated_data.pop('product_categories',None)
        scene_categories = validated_data.pop('scene_categories',None)
        scene_group = validated_data.pop('scene_group', None)
    
        if scene_group == '':
            scene.scene_group = None

        if scene_group:
            if settings.immersive_experience:
                raise serializers.ValidationError({"scene_group":[
                            "cannot assign scene_group when immersive experience is ON"
                            ]})
            else:
                try:
                    sceneGroupObj = SceneGroup.objects.get(id=scene_group)
                except SceneGroup.DoesNotExist:
                    raise serializers.ValidationError({"scene_group":[
                            "scene_group doesn't exist"
                            ]})
                except ValueError:
                    raise serializers.ValidationError({"scene_group":[
                            "expected an integer as value"
                            ]})

        if interactions == '':
            scene.call_to_actions.clear()
        if interactions:
            interactions = interactions.split(",")
            scene.call_to_actions.clear()
            for i in interactions:
                    try:
                        obj = CallToActionPro.objects.get(id=i)
                    except CallToActionPro.DoesNotExist:
                        raise serializers.ValidationError({"interactions":[
                            "interactions doesn't exist"
                            ]})
                    except:
                        raise serializers.ValidationError({"interactions":[
                            f"interactions expected an integer but got '{i}'"
                            ]})
                    scene.call_to_actions.add(obj)
        
        if product_categories == '':
            scene.tech_and_digital_services_tier_1.clear()
        if product_categories:
            product_categories = product_categories.split(",")
            scene.tech_and_digital_services_tier_1.clear()
            for i in product_categories:
                    try:
                        obj = ProductTier1.objects.get(id=i)
                    except ProductTier1.DoesNotExist:
                        raise serializers.ValidationError({"product_categories":[
                            "product_categories doesn't exist"
                            ]})
                    except:
                        raise serializers.ValidationError({"product_categories":[
                            f"product_categories expected an integer but got '{i}'"
                            ]})
                    scene.tech_and_digital_services_tier_1.add(obj)
        
        if scene_categories == '':
            scene.sectors_and_departments.clear()
        if scene_categories:
            scene_categories = scene_categories.split(",")
            scene.sectors_and_departments.clear()
            for i in scene_categories:
                    try:
                        obj = Sector.objects.get(id=i)
                    except Sector.DoesNotExist:
                        raise serializers.ValidationError({"scene_categories":[
                            "scene_categories doesn't exist"
                            ]})
                    except:
                        raise serializers.ValidationError({"scene_categories":[
                            f"scene_categories expected an integer but got '{i}'"
                            ]})
                    scene.sectors_and_departments.add(obj)

        scene = super().update(instance, validated_data)
        
        if scene_group:
            scene.scene_group = sceneGroupObj
            scene.save()
        
        return scene
    
    def validate_unity_scene_version(self, unity_scene_version):
        unity_scene = self.initial_data.get('unity_scene')
        try:
            if unity_scene_version is None:
                return unity_scene_version
            else:
                unity_scene_version = UnitySceneVersion.objects.get(id=unity_scene_version, unity_scene=unity_scene)
        except UnitySceneVersion.DoesNotExist:
            raise serializers.ValidationError("unity scene version with this id was not found")
        
        if unity_scene_version.deleted_at is None:
            return unity_scene_version
        else:
            raise serializers.ValidationError('cannot select a deleted unity scene version')


    def validate_unity_scene(self, unity_scene):
        try:
            if unity_scene is None:
                return unity_scene
            else:
                unityScene = UnityScene.objects.get(id=unity_scene)
        except:
            raise serializers.ValidationError("unity scene with this id was not found")
        
        if unityScene.deleted_at is None:
            scene = Scene.objects.filter(deleted_at__isnull=True)
            itself = self.instance.id
            for i in scene:
                if i.unity_scene == unityScene:
                        if itself == i.id:
                            return unityScene
                        else:
                            raise serializers.ValidationError("unity_scene with this id is already associated with a scene")
            return unityScene
        else:
            raise serializers.ValidationError("cannot select a unity scene that is deleted")
            
    def validate_image(self, image):
        try:
            img = Image.open(image)
        except Exception as e:
            raise serializers.ValidationError("not a valid image file")

        if img.format.lower() not in ['jpeg', 'png', 'svg', 'jpg']:
            raise serializers.ValidationError("image file format not supported only ( jpeg, jpg, svg, png ) allowed")
        return image

#--------------------------------------------------------------------------------
# FILE SERIALIZER
#--------------------------------------------------------------------------------
class FileLibrarySerializer(serializers.ModelSerializer):
    parent = serializers.StringRelatedField()
    class Meta:
        model = FileLibrary
        fields = [
            'id',
            'name',
            'parent'
        ]

    def validate_name(self, name):
        if name == "File Library":
            raise serializers.ValidationError("cannot use that name")
        return name
        
        
class FileLibraryUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    class Meta:
        model = FileLibrary
        fields = [
            'name'
        ]

    def validate_name(self, name):
        if name == "rootFolder":
            raise serializers.ValidationError("cannot use that name")
        return name
        

class Model3DSerializer(serializers.ModelSerializer):
    folder = serializers.StringRelatedField()
    class Meta:
        model = Model3D
        fields = [
            'id',
            'file',
            'folder'
        ]

    def validate_file(self, file):
        ext = os.path.splitext(file.name)[1]
        if not ext.lower() in ['.fbx', '.gltf', '.glb']:
            raise serializers.ValidationError("not a valid file format only ( .FBX, .gltf, .glb ) are supported")
        return file



#--------------------------------------------------------------------------------
# SETTINGS SERIALIZER
#--------------------------------------------------------------------------------
class SettingsSerializer(serializers.ModelSerializer):

    interactions = serializers.CharField(source='cta')
    categories = serializers.CharField(source='sector')
    product_categories = serializers.CharField(source='product_tier_1')
    product = serializers.CharField(source='product_entities_tier_3')

    class Meta:
        model = SiteConfig
        fields = [
            'title',
            'contact_number',
            'navbar_logo',
            'favicon',
            'holobite_name',
            'holobite_display',
            'analytics_header',
            'analytics_body',
            'analytics_footer',
            'loading_image',
            'default_loading_text',
            'interactions',
            'categories',
            'product_categories',
            'product',
            'scene',
            'immersive_experience',
            'browse_without_login',
            'default_scene'
        ]

class SettingsUpdateSerializer(serializers.ModelSerializer):

    interactions = serializers.CharField(source='cta')
    categories = serializers.CharField(source='sector')
    product_categories = serializers.CharField(source='product_tier_1')
    product = serializers.CharField(source='product_entities_tier_3')
    default_scene = serializers.IntegerField(write_only=True)
    loading_image = serializers.FileField(required=False)

    class Meta:
        model = SiteConfig
        fields = [
            'title',
            'contact_number',
            'navbar_logo',
            'favicon',
            'holobite_name',
            'holobite_display',
            'analytics_header',
            'analytics_body',
            'analytics_footer',
            'loading_image',
            'default_loading_text',
            'interactions',
            'categories',
            'product_categories',
            'product',
            'scene',
            'immersive_experience',
            'browse_without_login',
            'default_scene'
        ]

    def update(self, instance, validated_data):
        instance = self.instance
        loading_image = validated_data.pop("loading_image", None)

        if loading_image:
            instance.loading_image = loading_image
        else:
            instance.loading_image = None

        return super().update(instance, validated_data)
    
    def validate_default_scene(self, default_scene):
        if Scene.objects.filter(id=default_scene, deleted_at__isnull=True).exists():
            scene = Scene.objects.get(id=default_scene)
            return scene
        else:
            raise serializers.ValidationError({"error":"scene ID not valid"})
    
    def validate_favicon(self, favicon):
        try:
            icon = Image.open(favicon)
        except Exception as e:
            raise serializers.ValidationError({"error":"not a valid icon file"})
        
        if icon.format.lower() not in ['png']:
            raise serializers.ValidationError({"error":"image format for icon of .png only allowed"})
        return favicon

    # def validate_contact_number(self, contact_number):
    #     if not contact_number.isnumeric():
    #         raise serializers.ValidationError({"error":"contact number invalid"})
    #     return contact_number
    

    def validate_loading_image(self, loading_image):
        if not loading_image:
            return loading_image

        ext = os.path.splitext(loading_image.name)[1].lower()

        if not ext in ['.jpeg', '.png', '.svg', '.jpg']:
            raise serializers.ValidationError('image file format not supported only ( jpeg, jpg, svg, png ) allowed')

        try:
            with Image.open(loading_image) as img:
                img.verify()
        except Exception:
            raise serializers.ValidationError('file is not a valid image.')

        return loading_image

    def validate_navbar_logo(self, navbar_logo):
        ext = os.path.splitext(navbar_logo.name)[1].lower()

        if not ext in ['.jpeg', '.png', '.svg', '.jpg']:
            raise serializers.ValidationError('image file format not supported only ( jpeg, jpg, svg, png ) allowed')

        try:
            with Image.open(navbar_logo) as img:
                img.verify()
        except Exception:
            raise serializers.ValidationError('file is not a valid image.')
        
        return navbar_logo
    
 

class HomePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePageOption
        fields = [
            'option',
            'image',
            'scene',
            'video_embed_code',
            # 'view_type',
        ]


class HomePageUpdateSerializer(serializers.ModelSerializer):
    scene = serializers.IntegerField(write_only = True, required = False)
    image = serializers.ImageField(write_only = True, required = False)
    class Meta:
        model = HomePageOption
        fields = [
            'option',
            'image',
            'scene',
            'video_embed_code',
            # 'view_type',
        ]

    def update(self, instance, validated_data):
        instance = HomePageOption.objects.first()
        image = validated_data.pop('image', 'null')
        scene = validated_data.pop('scene', None)
        video_embed_code = validated_data.pop('video_embed_code', None)
        if image != 'null':
            instance.option = 'IMAGE'
            instance.image = image
        elif scene:
            instance.option = 'SCENE'
            instance.scene = scene
        elif video_embed_code:
            instance.option = 'VIDEO'
            instance.video_embed_code = video_embed_code
        else:
            if image == 'null':
                instance.image = None
        return super().update(instance, validated_data)
    
    def validate(self, attrs):
        image = attrs.get('image')
        scene = attrs.get('scene')
        video_embed_code = attrs.get('video_embed_code')
        
        if image and (scene or video_embed_code):
            raise serializers.ValidationError("Image option cannot have a scene or video embed code")
        elif scene and (image or video_embed_code):
            raise serializers.ValidationError("Scene option cannot have an image or video embed code")
        elif video_embed_code and (image or scene):
            raise serializers.ValidationError("Video option cannot have an image or scene")
        return attrs

    def validate_scene(self, scene):
        try:
            scene = UnityScene.objects.get(id=scene)
        except:
            raise serializers.ValidationError("unity scene does not exist")
        
        if scene.deleted_at is not None:
            raise serializers.ValidationError("cannot set deleted unity scene as homepage")
        else:
            return scene
            
    def validate_image(self, image):
        try:
            img = Image.open(image)
        except Exception as e:
            raise serializers.ValidationError("not a valid image file")

        if img.format.lower() not in ['jpeg', 'png', 'svg', 'jpg']:
            raise serializers.ValidationError("image file format not supported only ( jpeg, jpg, svg, png ) allowed")
        return image
    
class FilterIconSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterIcon
        fields = [
            "teleportation_icon",
            "revenue_stack_icon",
            "geo_dot_icon",
            "video_icon",
            "annotation_icon",
            "product_icon",
        ]

    
class FilterIconUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterIcon
        fields = [
            "teleportation_icon",
            "revenue_stack_icon",
            "geo_dot_icon",
            "video_icon",
            "annotation_icon",
            "product_icon",
        ]

    def validate(self, data):
        for field_name in self.fields:
            icon = data.get(field_name)
            if icon:
                try:
                    with Image.open(icon) as img:
                        pass
                except IOError:
                    raise serializers.ValidationError(f"{field_name} should be an image.")
        return data
    

class FilterActionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='text')
    class Meta:
        model = ActionType
        fields = [
            "id",
            "name",
            "value",
            "show_in_filter"
        ]    


class ShareIconSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareIcon
        fields = [
            "show_facebook",
            # "facebook_icon",
            "show_twitter",
            # "twitter_icon",
            "show_linkedin",
            # "linkedin_icon",
            "show_pinterest",
            # "pinterest_icon",
            "show_email",
            # "email_icon",
            "show_copy_link"
        ]


# class ShareIconUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ShareIcon
#         fields = [
#             "show_facebook",
#             "facebook_icon",
#             "show_twitter",
#             "twitter_icon",
#             "show_linkedin",
#             "linkedin_icon",
#             "show_pinterest",
#             "pinterest_icon",
#             "show_email",
#             "email_icon",
#             "show_copy_link"
#         ]
    
    # def validate_image(self, data):
    #     for field_name in self.fields:
    #         icon = data.get(field_name)
    #         if icon:
    #             try:
    #                 with Image.open(icon) as img:
    #                     pass
    #             except IOError:
    #                 raise serializers.ValidationError(f"{field_name} should be an image.")
    #     return data
    

class SceneGroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False, error_messages={'required': 'Name field is required', 'blank': 'Name field cannot be blank'})
    color = serializers.CharField(required=True, allow_blank=False, error_messages={'required': 'Color field is required', 'blank': 'Color field cannot be blank'})

    class Meta:
        model = SceneGroup
        fields = [
            'id',
            'name',
            'color'
        ]

    def create(self, validated_data):
        if 'name' in validated_data:
            validated_data['slug'] = slugify(validated_data['name'])
        instance = super().create(validated_data)
        return instance

