from bm.gallery import models as galmodels
from django.contrib import admin


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'url', 'num_pictures')
    search_fields = ('user__username',)

    def num_pictures(self, profile):
        return galmodels.Photo.objects.filter(owner=profile.user).count()


class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'year', 'image_link',)
    search_fields = ('title', 'year', 'owner__username',)

    def image_link(self, image):
      return '<a href="%s">%s</a>' % (image.image.url, image.image.url)
    image_link.allow_tags = True


class PhotoAdmin(ImageAdmin):
    list_display = ('id', 'title', 'year', 'image_link', 'in_press_gallery',)


admin.site.register(galmodels.Photo, PhotoAdmin)
admin.site.register(galmodels.Artifact, ImageAdmin)
admin.site.register(galmodels.Video)
admin.site.register(galmodels.Profile, ProfileAdmin)

