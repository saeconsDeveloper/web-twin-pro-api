from base64 import b32encode
from urllib.parse import quote, urlencode
from django.conf import settings
from django.db import models
from django_otp.plugins.otp_totp.models import TOTPDevice


class ProxyTOTPDevice(TOTPDevice):
	class Meta:
		proxy = True

	@property
	def config_url(self):
		"""
		THIS METHOD IS OVERRIDE FROM TOTPDevice to create custom label

		# TOTPDevice:
		A URL for configuring Google Authenticator or similar.

		See https://github.com/google/google-authenticator/wiki/Key-Uri-Format.
		The issuer is taken from :setting:`OTP_TOTP_ISSUER`, if available.

		"""
		label = 'Neom: {}'.format(self.user.get_username())
		params = {
			'secret': b32encode(self.bin_key),
			'algorithm': 'SHA1',
			'digits': self.digits,
			'period': self.step,
		}
		urlencoded_params = urlencode(params)

		issuer = getattr(settings, 'OTP_TOTP_ISSUER', None)
		if callable(issuer):
			issuer = issuer(self)
		if isinstance(issuer, str) and (issuer != ''):
			issuer = issuer.replace(':', '')
			label = '{}:{}'.format(issuer, label)
			urlencoded_params += '&issuer={}'.format(quote(issuer))  # encode issuer as per RFC 3986, not quote_plus

		url = 'otpauth://totp/{}?{}'.format(quote(label), urlencoded_params)

		return url