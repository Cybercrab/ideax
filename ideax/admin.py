from django.contrib import admin
from .models import Idea, UserProfile, Popular_Vote, Comment, Category, Dimension, Category_Dimension, Evaluation, Category_Image, Use_Term, Challenge
from django.contrib.auth.models import Permission
from martor.widgets import AdminMartorWidget
from martor.models import MartorField

class IdeaAdmin(admin.ModelAdmin):
    list_display = []
    formfield_overrides = {
        MartorField: {'widget': AdminMartorWidget},
}

admin.site.register(Idea, IdeaAdmin)
admin.site.register(UserProfile)
admin.site.register(Popular_Vote)
admin.site.register(Comment)
admin.site.register(Category)
admin.site.register(Dimension)
admin.site.register(Category_Dimension)
admin.site.register(Evaluation)
admin.site.register(Category_Image)
admin.site.register(Use_Term)
admin.site.register(Permission)
admin.site.register(Challenge)
