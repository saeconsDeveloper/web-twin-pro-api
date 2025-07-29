from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.validators import FileExtensionValidator
from django.db import IntegrityError, models
from django.utils import timezone
from slugify import slugify

from .services import get_random_position


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


# Audit Log which records transactions
class AuditTrail(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    model_type = models.CharField("Model Type", max_length=255)
    object_id = models.IntegerField("Model Id")
    object_str = models.CharField("Model Str", max_length=255)
    action = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True)
    instance = models.JSONField(null=True)
    previous_instance = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.model_type)


class DateTimeModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        auto_now=False,
    )
    updated_at = models.DateTimeField(
        auto_now_add=False,
        auto_now=True,
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, hard=False):
        if not hard:
            self.deleted_at = timezone.now()
            super().save()
        else:
            super().delete()


class ActionType(DateTimeModel):
    text = models.CharField(max_length=255)
    value = models.CharField(max_length=255, null=True, blank=True)
    show_in_filter = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class CallToAction(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255, null=True, blank=True)
    action_type = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if not self.name:
            return "button -> {} -> {}".format(
                self.get_action_type_text(self.action_type), self.directus_id
            )
        return "{} -> {}".format(self.get_action_type_text(self.action_type), self.name)

    def get_action_type_text(self, action_type):
        action_type_qs = ActionType.objects.filter(
            deleted_at__isnull=True, value=action_type
        )
        if not action_type_qs.exists():
            return action_type
        return action_type_qs.first().text


class CallToActionPro(DateTimeModel):
    name = models.CharField(max_length=255)
    action_type = models.ForeignKey(
        ActionType, related_name="call_to_actions_pro", on_delete=models.CASCADE
    )
    unity_scene_annotation_id = models.CharField(
        "Unity Scene Annotation Id", max_length=255, null=True, blank=True
    )
    annotation_title = models.CharField(max_length=255, null=True, blank=True)
    unity_scene_teleportation_id = models.CharField(
        "Unity Scene Teleportation Id", max_length=255, null=True, blank=True
    )
    unity_scene_video_id = models.CharField(
        "Unity Scene Video Id", max_length=255, null=True, blank=True
    )
    revenue_stack_number = models.PositiveIntegerField(
        "Revenue Stack Number", null=True, blank=True
    )
    embed_link = models.CharField(
        "Video Embed Link", max_length=255, null=True, blank=True
    )
    wtp_scene_id = models.PositiveIntegerField("WTP Scene Id", null=True, blank=True)
    wtp_scene_name = models.CharField(
        "WTP Scene Name", max_length=255, null=True, blank=True
    )
    scene = models.ForeignKey(
        "Scene",
        related_name="call_to_actions_pro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="call-to-action-pro", null=True, blank=True)
    status = models.CharField(
        max_length=255,
        choices=(("DRAFT", "Draft"), ("PUBLISHED", "Published")),
        default="DRAFT",
    )
    # hidden_fields
    top = models.PositiveIntegerField(null=True, blank=True)
    left = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Call to action pro"
        verbose_name_plural = "Call to actions pro"
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if self.left == None or self.top == None:
            self.left, self.top = get_random_position()
        return super().save(*args, **kwargs)

    def get_position_obj(self):
        if not hasattr(self, "position_obj"):
            self.position_obj = self.position.all().first()
        return self.position_obj

    def get_position_x(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_x
        return self.left

    def get_position_y(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_y
        return self.top

    def __str__(self):
        name = (
            f"{self.name} ({self.status})" if self.status == "DRAFT" else f"{self.name}"
        )
        return name


class CallToActionProPosition(DateTimeModel):
    call_to_actions = models.ForeignKey(
        CallToActionPro, related_name="position", on_delete=models.CASCADE
    )
    scene_id = models.PositiveIntegerField()
    position_x = models.PositiveIntegerField()
    position_y = models.PositiveIntegerField()


class Legend(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class BuildYourExperience(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class MetaPanelLink(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class MetaPanelImage(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Sector(DateTimeModel):
    name = models.CharField(max_length=255)
    category_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=255,
        choices=(("DRAFT", "Draft"), ("PUBLISHED", "Published")),
        default="DRAFT",
    )
    image = models.FileField("Icon", upload_to="sector/images", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    banner_image = models.FileField("Mobile Banner Image", upload_to="sector/images")
    slug = models.SlugField(unique=True, null=True, blank=True)
    show_in_filter = models.BooleanField(default=False)

    # hidden fields
    position_x = models.PositiveIntegerField(null=True, blank=True)
    position_y = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Sector"
        verbose_name_plural = "Sectors"

    def save(self, *args, **kwargs):
        if self.position_x == None or self.position_y == None:
            self.position_x, self.position_y = get_random_position()
        return super().save(*args, **kwargs)

    def get_image_url(self):
        if self.image not in [None, ""]:
            return self.image.url
        return "/static/scenes_v2/assets/images/construction.svg"

    def get_experience_count(self):
        return (
            self.sector_scenes.filter(
                deleted_at__isnull=True, status="PUBLISHED", scene_group__isnull=False
            )
            .values_list("scene_group", flat=True)
            .distinct()
            .count()
        )

    def __str__(self):
        return self.name


class Scene(DateTimeModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=255,
        choices=(("DRAFT", "Draft"), ("PUBLISHED", "Published")),
        default="DRAFT",
    )
    unity_scene = models.ForeignKey(
        "UnityScene",
        related_name="scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    unity_scene_version = models.ForeignKey(
        "UnitySceneVersion",
        related_name="scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    web_url = models.CharField("Web Url", max_length=255, null=True, blank=True)
    image = models.FileField(upload_to="scene/images")
    description = models.CharField(max_length=255)
    previous = models.ForeignKey(
        "self",
        related_name="nextscenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    next = models.ForeignKey(
        "self",
        related_name="previousscenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    # call_to_actions = models.ManyToManyField(CallToAction, verbose_name='Buttons', blank=True)
    call_to_actions = models.ManyToManyField(
        CallToActionPro,
        related_name="scenes",
        verbose_name="Call-to-actions",
        blank=True,
    )
    legend = models.ForeignKey(
        Legend, related_name="scenes", on_delete=models.CASCADE, null=True, blank=True
    )
    build_your_experience = models.ForeignKey(
        BuildYourExperience,
        verbose_name="Call-to-Actions",
        related_name="scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        "self",
        related_name="children_scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    meta_panel_links = models.ForeignKey(
        MetaPanelLink,
        related_name="scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    meta_panel_images = models.ForeignKey(
        MetaPanelImage,
        related_name="scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    geography = models.ForeignKey(
        "Geography",
        related_name="scenes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    tech_and_digital_services = models.ManyToManyField(
        "ProductPanel", related_name="product_scenes", blank=True
    )
    tech_and_digital_services_tier_1 = models.ManyToManyField(
        "ProductTier1", related_name="+", blank=True
    )
    # sectors_and_departments = models.ManyToManyField(SectorAndDepartment, related_name="sector_scenes", blank=True)
    sectors_and_departments = models.ManyToManyField(
        Sector, related_name="sector_scenes", blank=True
    )
    scene_group = models.ForeignKey(
        "SceneGroup",
        verbose_name="Group",
        related_name="scenes",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    priority = models.PositiveIntegerField("Group Order", default=0)

    class Meta:
        ordering = ["priority", "-created_at"]
        verbose_name = "Scene"
        verbose_name_plural = "Scenes"

    def __str__(self):
        return self.title

    @classmethod
    def get_default(cls):
        if not cls.objects.filter(deleted_at__isnull=True).exists():
            return None
        scene_obj = cls.objects.filter(deleted_at__isnull=True).first()
        return scene_obj.pk


class Geography(DateTimeModel):
    display_name = models.CharField(max_length=255)
    display_image = models.ImageField(
        upload_to="geographies/images", null=True, blank=True
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    robotics_image = models.ImageField(
        "Robotics Image", upload_to="geographies/robotics/images", null=True, blank=True
    )
    robotics_scene = models.ForeignKey(
        Scene,
        related_name="roboticsscenegeographies",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    visitors_image = models.ImageField(
        "Visitors Image", upload_to="geographies/robotics/images", null=True, blank=True
    )
    visitors_scene = models.ForeignKey(
        Scene,
        related_name="visitorsscenegeographies",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=255,
        choices=(("DRAFT", "Draft"), ("PUBLISHED", "Published")),
        default="DRAFT",
    )
    scene_children = models.ManyToManyField(
        Scene, related_name="parent_scene_geography", blank=True
    )

    class Meta:
        ordering = ["display_name"]
        verbose_name = "Geography"
        verbose_name_plural = "Geographies"

    def __str__(self):
        return self.display_name

    def get_all_scene_children(self):
        if not hasattr(self, "all_scene_children"):
            self.all_scene_children = Scene.objects.filter(
                id__in=self.scene_children
            ).order_by()
        return self.all_scene_children


class UnityScene(DateTimeModel):
    name = models.CharField(max_length=255)
    background_image = models.ImageField(
        "Loading Image",
        upload_to="unity/images",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "svg", "jpg", "jpeg"])
        ],
    )
    loading_text = models.CharField(max_length=1024, null=True, blank=True)
    unity_file = models.FileField(
        upload_to="unity/zips",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "zip",
                ]
            )
        ],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Unity Scene"
        verbose_name_plural = "Unity Scenes"

    def __str__(self):
        return self.name


class UnitySceneVersion(DateTimeModel):
    unity_scene = models.ForeignKey(
        UnityScene, related_name="versions", on_delete=models.CASCADE
    )
    version = models.CharField("Version name", max_length=255)
    content_json = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["version"]
        verbose_name = "Unity Scene version"
        verbose_name_plural = "Unity Scene versions"

    def __str__(self):
        return self.version


class Service(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=2048, null=True, blank=True)
    image_url = models.CharField(max_length=255, null=True, blank=True)
    icon_url = models.CharField(max_length=255, null=True, blank=True)
    subcategories = models.ManyToManyField("ServiceSubCategory", blank=True)
    show_in_filter = models.BooleanField(default=False)

    # hidden  field
    position_x = models.PositiveIntegerField(null=True, blank=True)
    position_y = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.position_x == None or self.position_y == None:
            self.position_x, self.position_y = get_random_position()
        return super().save(*args, **kwargs)

    def get_position_obj(self):
        if not hasattr(self, "position_obj"):
            self.position_obj = self.position.all().first()
        return self.position_obj

    def get_position_x(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_x
        return self.position_x

    def get_position_y(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_y
        return self.position_y

    # def get_service_image(self):
    #     if not self.image_url:
    #         try:
    #             service_detail = get_service_detail(self.directus_id)
    #             image_url = service_detail['data']['image']['id']
    #         except Exception as e:
    #             print(e, type(e))
    #             image_url = None
    #         self.image_url = image_url
    #     return self.image_url


class ServicePosition(DateTimeModel):
    service = models.ForeignKey(
        Service, related_name="position", on_delete=models.CASCADE
    )
    scene_id = models.PositiveIntegerField()
    position_x = models.PositiveIntegerField()
    position_y = models.PositiveIntegerField()


class ProductTier1(DateTimeModel):
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=255,
        choices=(("DRAFT", "Draft"), ("PUBLISHED", "Published")),
        default="DRAFT",
    )
    sector = models.ForeignKey(
        "Sector",
        related_name="tier1_products",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    image = models.FileField("Image", upload_to="tier1-products", null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    model_3d = models.FileField(
        "Panel 3D Model (.FBX, .gltf, .glb)",
        upload_to="models",
        null=True,
        blank=True,
        help_text="Please embed your textures into the 3D model file and use correct procedure.",
    )
    product_button_id = models.CharField(max_length=255, null=True, blank=True)

    icon_image = models.ImageField(
        "Icon", upload_to="tier1-products", null=True, blank=True
    )

    # filter
    show_in_filter = models.BooleanField(default=False)

    # hidden  field
    position_x = models.PositiveIntegerField(null=True, blank=True)
    position_y = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ProductTier1"
        verbose_name_plural = "ProductsTier1"

    def __str__(self):
        name = (
            f"{self.name} ({self.status})" if self.status == "DRAFT" else f"{self.name}"
        )
        return name

    def save(self, *args, **kwargs):
        if self.position_x == None or self.position_y == None:
            self.position_x, self.position_y = get_random_position()
        return super().save(*args, **kwargs)

    def get_position_obj(self):
        if not hasattr(self, "position_obj"):
            self.position_obj = self.position.all().first()
        return self.position_obj

    def get_position_x(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_x
        return self.position_x

    def get_position_y(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_y
        return self.position_y


class ProductTier1Position(DateTimeModel):
    product_tier_1 = models.ForeignKey(
        ProductTier1, related_name="position", on_delete=models.CASCADE
    )
    scene_id = models.PositiveIntegerField()
    position_x = models.PositiveIntegerField()
    position_y = models.PositiveIntegerField()


class ServiceSubCategory(DateTimeModel):
    directus_id = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    # hidden  field
    position_x = models.PositiveIntegerField(null=True, blank=True)
    position_y = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.position_x == None or self.position_y == None:
            self.position_x, self.position_y = get_random_position()
        return super().save(*args, **kwargs)

    def get_position_obj(self):
        if not hasattr(self, "position_obj"):
            self.position_obj = self.position.all().first()
        return self.position_obj

    def get_position_x(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_x
        return self.position_x

    def get_position_y(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_y
        return self.position_y


class SubCategoryPosition(DateTimeModel):
    subcategory = models.ForeignKey(
        ServiceSubCategory, related_name="position", on_delete=models.CASCADE
    )
    scene_id = models.PositiveIntegerField()
    position_x = models.PositiveIntegerField()
    position_y = models.PositiveIntegerField()


class ProductPanel(DateTimeModel):
    # t_and_d_function = models.CharField('Function Name', max_length=255)
    # t_and_d_function_description = models.CharField('Function Description', max_length=600)
    service = models.ForeignKey(
        ProductTier1,
        verbose_name="Product Categories Tiers 1",
        related_name="product_panels",
        on_delete=models.SET_NULL,
        null=True,
    )
    subcategory = models.ManyToManyField(
        ServiceSubCategory,
        verbose_name="Product Sub Categories Tiers 2",
        related_name="product_panels",
        blank=True,
    )
    display_text = models.CharField("Name", max_length=255)
    # panel_image = models.ImageField('Image', upload_to='panels', null=True, blank=True)
    hyperlink = models.CharField(max_length=255, null=True, blank=True)
    product_description = models.CharField("Description", max_length=600)
    model_3d = models.FileField(
        "Panel 3D Model (.FBX, .gltf, .glb)",
        upload_to="models",
        null=True,
        blank=True,
        help_text="Please embed your textures into the 3D model file and use correct procedure.",
    )
    asset = models.CharField(
        "Vendor's Service name", max_length=255, null=True, blank=True
    )
    asset_description = models.CharField(
        "Vendor's Service description", max_length=1500, null=True, blank=True
    )
    pricing_of_tiers = models.CharField("Price", max_length=255, null=True, blank=True)
    vendor = models.CharField("Vendor Name", max_length=255, null=True, blank=True)
    priority = models.CharField(
        max_length=255,
        choices=(
            ("Low", "Low"),
            ("Medium", "Medium"),
            ("High", "High"),
        ),
        null=True,
        blank=True,
    )
    service_owner = models.CharField(
        "Manager's Name", max_length=255, null=True, blank=True
    )
    how_to_request = models.CharField(
        "How to Request", max_length=255, null=True, blank=True
    )

    # hidden  field
    position_x = models.PositiveIntegerField(null=True, blank=True)
    position_y = models.PositiveIntegerField(null=True, blank=True)

    # new slug field
    slug = models.SlugField(unique=True, null=True, blank=True)

    status = models.CharField(
        max_length=255,
        choices=(("DRAFT", "Draft"), ("PUBLISHED", "Published")),
        default="DRAFT",
    )

    def __str__(self) -> str:
        if self.service:
            return "{} -> {}".format(self.service.name, self.display_text)
        return self.display_text

    def get_slug(self):
        if not self.slug:
            try:
                self.slug = slugify(self.display_text)
                self.save()
            except IntegrityError as e:
                self.slug = slugify(self.display_text) + "-{}".format(self.id)
                self.save()
        return self.slug

    def get_position_obj(self):
        if not hasattr(self, "position_obj"):
            self.position_obj = self.position.all().first()
        return self.position_obj

    def get_position_x(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_x
        return self.position_x

    def get_position_y(self):
        position_obj = self.get_position_obj()
        if position_obj != None:
            return position_obj.position_y
        return self.position_y


class ProductPanelPosition(DateTimeModel):
    product_panel = models.ForeignKey(
        ProductPanel, related_name="position", on_delete=models.CASCADE
    )
    scene_id = models.PositiveIntegerField()
    position_x = models.PositiveIntegerField()
    position_y = models.PositiveIntegerField()


class ProductPanelFilterSetting(DateTimeModel):
    product_panel = models.ForeignKey(ProductPanel, on_delete=models.CASCADE)
    sector_id = models.PositiveIntegerField()
    sector_name = models.CharField(max_length=255, null=True, blank=True)
    scene_id = (
        models.PositiveIntegerField()
    )  # NOTE: scene is referred to discovery maps id (geography)
    scene_name = models.CharField(max_length=255, null=True, blank=True)
    launch_year = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    # enabled/disabled status
    is_disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return "{} -> {},{}".format(self.product_panel, self.sector_id, self.scene_id)


class UploadedFile(DateTimeModel):
    file = models.FileField(upload_to="files")

    def __str__(self):
        return self.file.path


class FileLibrary(DateTimeModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        related_name="sub_folders",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "FileLibrary"
        verbose_name_plural = "FileLibraries"

    def __str__(self):
        return self.name


# class Model3DState(models.Model):
#     state = models.CharField(max_length=100)

#     def __str__(self) -> str:
#         return self.state

# class Model3DEmote(models.Model):
#     emote = models.CharField(max_length=100)

#     def __str__(self) -> str:
#         return self.emote


class Model3D(DateTimeModel):
    file = models.FileField(
        "Panel 3D Model (.FBX, .gltf, .glb)",
        upload_to="models",
        help_text="Please embed your textures into the 3D model file and use correct procedure.",
    )
    # states = models.ManyToManyField(to=Model3DState, related_name='states', null=True, blank=True)
    # emotes = models.ManyToManyField(to=Model3DEmote, related_name='emotes', null=True, blank=True)

    folder = models.ForeignKey(
        FileLibrary,
        related_name="model3Ds",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return "{}, Size: {}{}, Image: {}".format(
            self.file_name, self.file_size, self.file_type, self.is_image
        )

    def get_human_readable_size(self):
        size = self.file.size
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
            if size < 1024.0 or unit == "PB":
                break
            size /= 1024.0
        return (round(size, 2), unit)

    @property
    def is_image(self):
        return self.file.url.split(".")[-1].lower() in ["jpeg", "jpg", "png", "gif"]

    @property
    def file_size(self):
        return self.get_human_readable_size()[0]

    @property
    def file_type(self):
        return self.file.url.split(".")[-1]

    @property
    def file_name(self):
        return self.file.name.replace("models/", "")


class SiteConfig(DateTimeModel):
    title = models.CharField("Title", max_length=255, null=True, blank=True)
    navbar_logo = models.FileField(
        "Navbar Logo", upload_to="configs", null=True, blank=True
    )
    favicon = models.FileField("Favicon", upload_to="configs", null=True, blank=True)
    holobite_name = models.CharField(
        "Holobite Name", max_length=255, null=True, blank=True
    )
    holobite_display = models.BooleanField("Display", default=False)
    annotation_filter = models.BooleanField(
        "Annotation", default=False
    )  # if true enable annotation filter
    show_mobile_version = models.BooleanField(
        "Show Mobile Version", default=False
    )  # if true enable mobile view
    # scene_groups = models.ManyToManyField('SceneGroup', verbose_name='Groups', null=True, blank=True)
    loading_image = models.FileField(
        "Loading Image", upload_to="configs", null=True, blank=True
    )
    default_loading_text = models.CharField(
        "Default Loading Text",
        max_length=255,
        null=True,
        blank=True,
        default="Loading scene...",
    )

    # analytics
    analytics_header = models.TextField("Analytics for Header", null=True, blank=True)
    analytics_body = models.TextField("Analytics for Body", null=True, blank=True)
    analytics_footer = models.TextField("Analytics for Footer", null=True, blank=True)

    # rename sections
    cta = models.CharField("Call to Action", max_length=255, default="Interactions")
    sector = models.CharField("Sector", max_length=255, default="Categories")
    product_tier_1 = models.CharField(
        "Product Tier 1", max_length=255, default="Product Categories"
    )
    product_entities_tier_3 = models.CharField(
        "Product Entities Tier 3", max_length=255, default="Products"
    )
    scene = models.CharField("Scene", max_length=255, default="Scene")

    contact_number = models.CharField(
        max_length=255, default="0800 100 392 121", null=True, blank=True
    )

    # immersive experience
    immersive_experience = models.BooleanField("Immersive Experience", default=False)

    # browse without login
    browse_without_login = models.BooleanField("Browse Without Login", default=False)

    # default scene
    default_scene = models.ForeignKey(
        Scene,
        related_name="default_scene",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=Scene.get_default,
    )

    # contact form recipients
    contact_form_recipients = models.JSONField(
        "Contact Form Recipients", null=True, blank=True
    )

    def __str__(self):
        return "Site Config Object"

    def get_contact_form_recipients(self):
        if not self.contact_form_recipients:
            return None
        return ", ".join(self.contact_form_recipients)

    def save(self, *args, **kwargs):
        if self.pk == None and SiteConfig.objects.all().count() > 0:
            return None
        return super().save(*args, **kwargs)

    @staticmethod
    def get_instance():
        if SiteConfig.has_object():
            return SiteConfig.objects.first()
        return SiteConfig()

    @staticmethod
    def has_object():
        return SiteConfig.objects.all().count() > 0


class SceneGroup(DateTimeModel):
    name = models.CharField("Name", max_length=255, null=True, blank=True)
    color = models.CharField(max_length=7, default="#123088")
    slug = models.SlugField(unique=True, null=True, blank=True)

    def __str__(self):
        if self.name:
            return self.name
        return self.color

    def save(self, *args, **kwargs):
        if self.slug == None:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def get_slug(self):
        if not self.slug:
            self.slug = slugify(self.name)
            self.save()
        return self.slug


class HomePageOption(DateTimeModel):
    option = models.CharField(
        "Option",
        choices=(("IMAGE", "Image"), ("SCENE", "Scene"), ("VIDEO", "Video")),
        default="IMAGE",
        max_length=255,
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="configs", null=True, blank=True)
    scene = models.ForeignKey(
        UnityScene,
        related_name="home_page_options",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    video_embed_code = models.TextField("Video/Audio Embed Code", null=True, blank=True)
    view_type = models.CharField(
        max_length=255,
        choices=(("NORMAL", "Normal"), ("GALLERY", "Gallery")),
        default="NORMAL",
    )

    def __str__(self):
        return "Home Page Option Object"

    def save(self, *args, **kwargs):
        if self.video_embed_code:
            if (
                "embed" not in self.video_embed_code
                and "youtube.com" in self.video_embed_code
            ):
                key = self.video_embed_code.split("?v=")
                if len(key) > 1:
                    self.video_embed_code = "https://www.youtube.com/embed/{}".format(
                        key[1]
                    )
        if self.pk == None and HomePageOption.objects.all().count() > 0:
            return None
        return super().save(*args, **kwargs)

    @staticmethod
    def get_instance():
        if HomePageOption.objects.first():
            return HomePageOption.objects.first()
        return HomePageOption()

    @staticmethod
    def has_object():
        return HomePageOption.objects.all().count() > 0


class ShareIcon(DateTimeModel):
    show_facebook = models.BooleanField(default=False)
    facebook_icon = models.ImageField(upload_to="configs", null=True, blank=True)
    show_twitter = models.BooleanField(default=False)
    twitter_icon = models.ImageField(upload_to="configs", null=True, blank=True)
    show_linkedin = models.BooleanField(default=False)
    linkedin_icon = models.ImageField(upload_to="configs", null=True, blank=True)
    show_pinterest = models.BooleanField(default=False)
    pinterest_icon = models.ImageField(upload_to="configs", null=True, blank=True)
    show_email = models.BooleanField(default=False)
    email_icon = models.ImageField(upload_to="configs", null=True, blank=True)
    show_copy_link = models.BooleanField(default=False)

    def __str__(self):
        return "Share Icon Option Object"

    def save(self, *args, **kwargs):
        if self.pk == None and ShareIcon.objects.all().count() > 0:
            return None
        return super().save(*args, **kwargs)

    @staticmethod
    def get_instance():
        if ShareIcon.objects.first():
            return ShareIcon.objects.first()
        return ShareIcon()

    @staticmethod
    def has_object():
        return ShareIcon.objects.all().count() > 0


# Theme Option
class ThemeOption(DateTimeModel):
    key = models.CharField(max_length=128)
    value = models.TextField()

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.key


# Filter Icon
class FilterIcon(DateTimeModel):
    teleportation_icon = models.FileField(
        upload_to="filter-icons", null=True, blank=True
    )
    revenue_stack_icon = models.FileField(
        upload_to="filter-icons", null=True, blank=True
    )
    geo_dot_icon = models.FileField(upload_to="filter-icons", null=True, blank=True)
    video_icon = models.FileField(upload_to="filter-icons", null=True, blank=True)
    annotation_icon = models.FileField(upload_to="filter-icons", null=True, blank=True)
    product_icon = models.FileField(upload_to="filter-icons", null=True, blank=True)
    image_icon = models.FileField(upload_to="filter-icons", null=True, blank=True)

    def __str__(self):
        return "Home Page Option Object"

    def save(self, *args, **kwargs):
        if self.pk == None and FilterIcon.objects.all().count() > 0:
            return None
        return super().save(*args, **kwargs)

    @staticmethod
    def get_instance():
        if FilterIcon.objects.first():
            return FilterIcon.objects.first()
        return FilterIcon()

    @staticmethod
    def has_object():
        return FilterIcon.objects.all().count() > 0
