- python 3.11.1

- Create a virtual environment using the ^ python version or later 
> python -m venv venv

- activate the virtual environment 
> venv\Scripts\activate

> pip install -r requirements.txt 

> python manage.py makemigrations 
> python manage.py makemigrations two_factor_auth
> python manage.py migrate 
> python manage.py loaddata fixtures/groups.json -> CREATES GROUPS [Superadmin, Uberadmin, Developer, Experience Designer]
> python manage.py loaddata fixtures/actions.json -> CREATES ACTION TYPES [Video, Teleportation, Annotation]



