
# pythonic-news
A Hacker News lookalike written in Python/Django, powering [https://news.python.sc](https://news.python.sc)



[![screenshot](http://cdn.sebastiansteins.com/screenshot-news-python-sc.png "Screenshot")](https://news.python.sc)


## Setup for local development

### Set up virtual environment
```shell script
python -m venv venv/
source venv/bin/activate(for activate the environmant)
deactivte(for deactivate the environment)
```

### Install Dependencies
```shell script
pip install -r requirements.txt
```

### Migrate Database
```shell script
python manage.py migrate
```

### Extra setup work
* Set ```DEBUG=True``` if necessary
* Add ```127.0.0.1``` to ```ALLOWED_HOSTS```

### Run Django Server
```shell script
python manage.py runserver
```
Now you can access the website at ```127.0.0.1:8000```.


