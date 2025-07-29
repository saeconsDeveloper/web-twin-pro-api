import json
import zipfile

from django.conf import settings
from django.conf import settings as conf_settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse

from dashboard.tokens import user_token

BASE_URL = settings.BASE_URL if hasattr(settings, 'BASE_URL') else ''

User = get_user_model()

def extract_unity_file(obj):
	with zipfile.ZipFile(obj.unity_file, 'r') as zip_ref:
	    zip_ref.extractall('media/unity/{}'.format(obj.name))


def reset_user_password(user, extra={}):
	'''
	Generates new random password for the user and sends email.
	'''
	password = get_random_string(length=12)
	user.set_password(password)
	html_message = (
		"You have been granted access to the Web Twin Pro with the following credentials: <br/><br/>" + 
		BASE_URL +"<br/><br/>" + 
		"<strong>Username: </strong>" + user.username + "<br/>" + 
		"<strong>Password: </strong>" + password  + "<br/>"
	)

	if user.groups.filter(name='Superadmin').exists():
		html_message += (
			"<br/>"+
			"Thank You!"
		)

	send_mail(
		subject="Your account on Web Twin Pro has been {}".format('created' if extra.get('created') else 'updated'), 
		message='', 
		from_email='{} <{}>'.format(conf_settings.EMAIL_DISPLAY_NAME, conf_settings.DEFAULT_FROM_EMAIL),
		recipient_list=[user.username], 
		fail_silently=True,
		html_message=html_message,
	)
	user.save(update_fields=["password"])


def send_reset_mail_for_email(user):
	'''
	Generated reset link for the user and sends email. 
	'''
	print('send_reset_mail_for_email {}'.format(user.email))
	idx, token = get_tokens_from_user(user)
	reset_url = BASE_URL + reverse('set-new-password', args=(idx, token, ))

	msg = (
		"You have just requested a password reset for the Web-Twin account associated with this email address. Please use the below link to reset your password.\n\n" + 
		reset_url
	)
	send_mail(
		subject="Your Web-Twin Password Reset Instructions", 
		message=msg, 
		from_email='{} <{}>'.format(conf_settings.EMAIL_DISPLAY_NAME, conf_settings.DEFAULT_FROM_EMAIL),
		recipient_list=[user.email], 
		fail_silently=False,
	)

def send_set_user_password_mail(user, extra={}):
	'''Generate set password url and send mail.'''
	idx, token = get_tokens_from_user(user)
	reset_url = BASE_URL + reverse('set-new-password', args=(idx, token, ))

	html_message = (
		"You have been granted access to the Web Twin Pro with the following credentials: <br/><br/>" + 
		BASE_URL +"<br/><br/>" + 
		"<strong>Username: </strong>" + user.username + "<br/>" + 
		"Please use the below link to set your password.\n\n" + 
		reset_url
	)

	send_mail(
		subject="Your account on Web Twin Pro has been {}".format('created' if extra.get('created') else 'updated'), 
		message=html_message, 
		from_email='{} <{}>'.format(conf_settings.EMAIL_DISPLAY_NAME, conf_settings.DEFAULT_FROM_EMAIL),
		recipient_list=[user.username], 
		fail_silently=False,
	)

def get_tokens_from_user(user):
	'''
	returns idx and token from the user
	'''
	user_details_json = json.dumps({ 'pk': user.pk, 'username': user.username })
	idx = urlsafe_base64_encode(force_bytes(user_details_json))
	token = user_token.make_token(user)
	return idx, token

def get_user_from_tokens(idx, token):
	'''
	checks idx and token for the user
	returns user if tokens are valid
	return None if tokens are not valid
	'''
	user_details = json.loads(force_str(urlsafe_base64_decode(idx)))
	if not User.objects.filter(**user_details).exists():
		raise Exception('Invalid idx')

	user = User.objects.filter(**user_details).first()
	if not user_token.check_token(user, token):
		raise Exception('Invalid token')

	return user

def get_scene_children(scene):
	if scene == None: 
		return []

	scene_children = [scene.pk]

	if scene.children_scenes.filter(deleted_at__isnull=True).exists():
		for child in scene.children_scenes.filter(deleted_at__isnull=True):
			scene_children += get_scene_children(child)
		return scene_children
	else:
		return scene_children

# def get_scene_children(scene, children=None):
# 	if children == None:
# 		children = []
	
# 	try:
# 		children_qs = scene.children_scene.filter(deleted_at__isnull=True)
# 	except AttributeError:
# 		return children
	
# 	for child in children_qs:
# 		children.extend(get_scene_children(child, children))
# 	print(children)
# 	return children
