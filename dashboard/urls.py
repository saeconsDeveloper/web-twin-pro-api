from django.urls import path

from dashboard import views

urlpatterns = [
    
    #AUDIT 
    path('audits', views.AuditListView.as_view(), name='audit-list'),

    #SEARCH
    path('search', views.SearchView.as_view(), name='search'),

    #CONTACT US
    path('contactus', views.ContactUs.as_view(), name='contact-us'),

    #USER CRUD
    path('user',views.UserView.as_view(),name='user'),
    path('users', views.UserListView.as_view(), name='users-list'),
    path('users/create', views.UserCreateView.as_view(), name='users-create'),
    path('users/<int:pk>/update', views.UserUpdateView.as_view(), name='users-update'),
    path('users/<int:pk>/status', views.UserStatusView.as_view(), name='users-status'),
    path('users/<int:pk>/password-reset', views.UserPasswordResetView.as_view(), name='users-password-reset'),

    #SCENES CRUD
    path('scenes', views.SceneListView.as_view(), name='scene-list'),
    path('scenes/<int:pk>', views.SceneDetailView.as_view(), name='scene-detail'),
    path('scenes/slug/<str:slug>', views.SceneSlugDetails.as_view(), name='scene-slug-details'),
    path('scenes/create', views.SceneCreateView.as_view(), name='scenes-create'),
    path("scenes/<int:pk>/update", views.SceneUpdateView.as_view(), name='scene-update'),
    path('scenes/<int:pk>/delete', views.SceneDeleteView.as_view(), name='scenes-delete'),

    #SCENES CATEGORIES
    path('scene-categories', views.SceneCategoriesListView.as_view(), name='scene-categories-list'),
    path('scene-categories/<int:pk>', views.SceneCategoriesDetailView.as_view(), name='scene-categories-detail'),
    path('scene-categories/create', views.SceneCategoriesCreateView.as_view(), name='scene-categories-create'),
    path('scene-categories/<int:pk>/update', views.SceneCategoriesUpdateView.as_view(), name='scene-categories-update'),
    path('scene-categories/<int:pk>/delete', views.SceneCategoriesDeleteView.as_view(), name='scene-categories-delete'),
    path('scene-categories/filter', views.SceneCategoriesFilter.as_view(), name='scene-categories-filter'),

    #UNITY SCENES CRUD
    path('unity-scenes',views.UnitySceneListView.as_view(), name='unity-scenes-list'),
    path('unity-scenes/create',views.UnitySceneCreateView.as_view(), name='unity-scenes-create'),
    path('unity-scenes/<int:pk>/update', views.UnitySceneUpdateView.as_view(), name='unity-scenes-update'),
    path('unity-scenes/<int:pk>/delete', views.UnitySceneDeleteView.as_view(), name='unity-scenes-delete'),

    #UNITY SCENES VERSION
    path('unity-scenes/<int:pk>/versions', views.UnitySceneVersionListView.as_view(), name='unity-scene-version-list'),
    path('unity-scenes/<int:pk>/versions/create', views.UnitySceneVersionCreateView.as_view(), name='unity-scene-version-create'),
    path('unity-scenes/<int:pk>/versions/<int:version_id>/update', views.UnitySceneVersionUpdateView.as_view(), name='unity-scene-version-update'),
    
    #PRODUCT
    path('product', views.ProductListView.as_view(), name='product'),
    path('product/<int:pk>', views.ProductDetailView.as_view(), name='product-detail'),
    path('product/create', views.ProductCreateView.as_view(), name='product-create'),
    path('product/<int:pk>/update', views.ProductUpdateView.as_view(), name='product-update'),
    path('product/<int:pk>/delete', views.ProductDeleteView.as_view(), name='product-delete'),

    #PRODUCT CATEGORIES
    path('product-categories', views.ProductCategoriesListView.as_view(), name='product-categories-list'),
    path('product-categories/<int:pk>', views.ProductCategoriesDetailView.as_view(), name='product-categories-detail'),
    path('product-categories/create', views.ProductCategoriesCreateView.as_view(), name='product-categories-create'),
    path('product-categories/<int:pk>/update', views.ProductCategoriesUpdateView.as_view(), name='product-categories-update'),
    path('product-categories/<int:pk>/delete',views.ProductCategoriesDeleteView.as_view(), name='product-categories-delete'),
    
    #INTERACTIONS
    path('interactions', views.InteractionsListView.as_view(), name='interactions-list'),
    path('interactions/<int:pk>', views.InteractionsDetailView.as_view(), name='interactions-detail'),
    path('interactions/create', views.InteractionsCreateView.as_view(), name='interactions-create'),
    path('interactions/<int:pk>/update', views.InteractionsUpdateView.as_view(), name='interactions-update'),
    path('interactions/<int:pk>/delete', views.InteractionsDeleteView.as_view(), name='interactions-delete'),

    #FILE LIBRARY
    path('file-library', views.FileLibraryView.as_view(), name='file-library'),
    path('file-library/<int:pk>', views.FileLibraryView.as_view(), name='file-library-create-sub-folder'),
    path('file-library/<int:pk>/detail', views.FileLibraryFolderDetailView.as_view(), name='file-library-folder-detail'),
    path('file-library/<int:pk>/update', views.FileLibraryUpdateView.as_view(), name='file-library-update'),
    path('file-library/<int:pk>/create', views.Model3DCreateView.as_view(), name='model3D-create'),
    path('file-library/<int:pk>/delete', views.Model3DDeleteView.as_view(), name='model3D-delete'),

    path('3dmodels',views.Model3DListView.as_view(), name='model3d-list'),

    #SETTINGS
    path('settings', views.SettingsView.as_view(), name='settings'),
    path('settings/homepage', views.HomePageSettingsView.as_view(), name='settings-homepage'),
    path('settings/theme', views.ThemeSettingView.as_view(), name='settings-theme'),
    path('settings/theme/filter-icons', views.FilterIconView.as_view(), name='filter-icons'),
    path('settings/share-icons', views.ShareIconView.as_view(), name='share-icons'),
    path('settings/filter-actions', views.FilterActionView.as_view(), name='filter-actions'),

    path('settings/scene-groups', views.SceneGroupView.as_view(), name='scene-groups'),
    path('settings/scene-groups/<int:pk>/update', views.SceneGroupUpdateView.as_view(), name='scene-groups-update'),
    path('settings/scene-groups/<int:pk>/delete', views.SceneGroupDeleteView.as_view(), name='scene-groups-delete'),

    #CONFIG
    path('config', views.ConfigView.as_view(), name='config'),

]
