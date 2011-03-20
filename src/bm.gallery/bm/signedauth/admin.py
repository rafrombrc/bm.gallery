from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from bm.signedauth.models import UserKey, WhitelistedIP

class UserKey_Inline(admin.StackedInline):
    model = UserKey
    max_num = 1
    readonly_fields = ('key','timestamp')

class WhitelistedIPAdmin(admin.ModelAdmin):
    list_fields = ('label','ip')

admin.site.unregister(User)

UserAdmin.inlines = (UserKey_Inline,)

admin.site.register(User, UserAdmin)
admin.site.register(WhitelistedIP, WhitelistedIPAdmin)
