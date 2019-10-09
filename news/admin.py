from django.contrib import admin


from .models import Story, Comment

admin.site.register(Story)
admin.site.register(Comment)