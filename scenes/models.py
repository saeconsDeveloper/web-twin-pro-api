from django.contrib.auth import get_user_model
from django.db import models

from dashboard.models import DateTimeModel

User = get_user_model()

class UserFilterSetting(DateTimeModel):
	user = models.OneToOneField(User, related_name='filter_setting', on_delete=models.CASCADE)
	settings_json = models.JSONField()

	def __str__(self):
		return '{}'.format(self.user)

	@classmethod
	def from_user(cls, user):
		if hasattr(user, 'filter_setting'):
			return user.filter_setting
		return None
