######
# For modifying breadcrumb and adding new_url
#######
from django.conf import settings
from django.shortcuts import get_object_or_404
# from directus_api.utils import get_discovery_map_from_scene
from dashboard.models import ProductPanel, ProductPanelFilterSetting, Scene


def modify_breadcrumb_with_new_url(breadcrumbs):
	url_append = '/scenes/neom'
	for item in breadcrumbs:
		url_append += '/' + item['slug']
		item['new_url'] = url_append
	return breadcrumbs

######
# For getting the append url for all elements
#######
def get_url_append_for_breadcrumb( breadcrumbs):
		url_append = '/scenes/neom'
		for item in breadcrumbs:
			url_append += '/'+item['slug']
		return url_append

def get_url_append_for_slug(slug):
	url_append = '/scene'
	url_append += '/'+slug
	return url_append


#
# product panel utils
def get_product_panel_settings(filter_params):
	sectors = filter_params.getlist('sectors[]')
	services = filter_params.getlist('services[]')
	scene_id = filter_params.get('scene')
	# status = filter_params.getlist('status[]')
	# launch_year = filter_params.getlist('year[]')

	# filtering
	# filter_qs = ProductPanelFilterSetting.objects.filter(
	# 	sector_name__in=sectors, 
	# 	# status__in=status, 
	# 	# launch_year__in=launch_year,
	# 	product_panel__service__name__in=services,
	# 	is_disabled=False,
	# )
	
	# if 'main_scene' in filter_params and filter_params.get('main_scene', '').isdigit():
	# 	# main_scene_id = int(filter_params.get('main_scene'))
	# 	# discovery_map_id = get_discovery_map_from_scene(main_scene_id)
	# 	main_scene = get_object_or_404(Scene, pk=int(filter_params.get('main_scene')))
	# 	discovery_map_id = main_scene.geography.id
	# 	if discovery_map_id != None:
	# 		filter_qs = filter_qs.filter(scene_id=discovery_map_id)
	# print('\n\n', filter_qs, 33333)
	scene = get_object_or_404(Scene, pk=int(filter_params.get('main_scene')))
	filter_qs = scene.tech_and_digital_services.filter(service__name__in=services)
	return filter_qs


def get_product_panels(filter_params, settings_qs=None):
	if settings_qs == None:
		settings_qs = get_product_panel_settings(filter_params)
	product_panels_id = list(settings_qs.values_list('id', flat=True).distinct())
	return ProductPanel.objects.filter(id__in=product_panels_id, deleted_at__isnull=True)
