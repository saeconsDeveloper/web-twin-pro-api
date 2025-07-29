import six
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class _UserTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp)
        )

user_token = _UserTokenGenerator()
