from bm.gallery import models as galmodels
from django.contrib import admin

admin.site.register(galmodels.Photo)
admin.site.register(galmodels.Artifact)
admin.site.register(galmodels.Video)
admin.site.register(galmodels.Profile)
