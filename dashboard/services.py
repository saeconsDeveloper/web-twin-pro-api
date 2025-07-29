import random
from urllib.parse import urlparse

def get_domain(url):
	parse_result = urlparse(url)
	return parse_result[1]

def get_random_position():
	""""
	placement:
	0 => left <= 30, top = any
	1 => left >= 70, top = any
	2 => left = any, top <= 30
	3 => left = any, top >= 70
	"""
	placement = random.randint(0, 3)
	position_x = 0
	position_y = 0
	if placement == 0:
		# print('0 => left <= 30, top = any')
		position_x = random.randint(5, 30)
		position_y = random.randint(5, 90)
	elif placement == 1:
		# print('1 => left >= 70, top = any')
		position_x = random.randint(70, 85)
		position_y = random.randint(5, 90)
	elif placement == 2:
		# print('2 => left = any, top <= 30')
		position_x = random.randint(5, 85)
		position_y = random.randint(5, 30)
	else:
		# print('3 => left = any, top >= 70')
		position_x = random.randint(5, 85)
		position_y = random.randint(70, 90)
	
	return position_x, position_y
	