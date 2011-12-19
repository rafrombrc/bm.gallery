from bm.gallery import models
from datetime import datetime
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import forms as authforms
from django.contrib.auth import models as authmodels
from django.forms import formsets
from django.utils.translation import ugettext_lazy as _
from tagging import forms as tagforms

mediachoices = [(key, value['title']) for key, value
                in models.mediatype_map.items()]

def clean(self):
    if any(self.errors):
        return
    if not any([form.cleaned_data for form in self.forms]):
        raise forms.ValidationError('Please upload at least one item.')


def clean_email(form):
    """Stolen from a StackOverflow response
    (http://tinyurl.com/25f5zlz).  We enforce email uniqueness
    at the form layer instead of the model b/c Django makes it
    harder than it should be to customize the core user model
    field definitions."""
    email = form.cleaned_data.get('email')
    username = form.cleaned_data.get('username')
    if username is None:
        username = form.instance.username
    existing = authmodels.User.objects.filter(email=email)
    existing = existing.exclude(username=username)
    if email and existing.count():
        raise forms.ValidationError(u'Email addresses must be unique.')
    return email


class MediaFormBase(forms.ModelForm):
    tags = tagforms.TagField(label=_("Keywords"), required=False)

    def __init__(self, *args, **kwargs):
        """Initialize the tags value"""
        retval = super(MediaFormBase, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance is not None:
            self.initial['tags'] = ' '.join([t.name for t in instance.tags])
        return retval

    def save(self, *args, **kwargs):
        """Write the tags value"""
        retval = super(MediaFormBase, self).save(*args, **kwargs)
        tags = self.cleaned_data['tags']
        self.instance.tags = tags
        # tagged objects can only be queried by model, so we also write
        # the tags to the mediabase model so we can query for all types
        # with a given tag
        self.instance.mediabase_ptr.tags = tags
        return retval

    def clean_year(self):
        """Ensure that we only allow valid years"""
        year = self.cleaned_data['year']
        min_year = 1986
        max_year = datetime.now().year
        if year < min_year or year > max_year:
            raise forms.ValidationError, ('Year value must be at least %d '
                                    'and no more than %d.') % (min_year,
                                                               max_year)
        return year


class ArtifactForm(MediaFormBase):
    class Meta:
        model = models.Artifact
        fields = ('title', 'notes', 'year', 'tags', 'image', 'categories')
        widgets = {'notes': forms.Textarea(attrs={'cols': 60, 'rows': 5})}


class ArtifactFormNoFile(MediaFormBase):
    notes = forms.CharField(widget = forms.Textarea(attrs={'cols': 60, 'rows': 5}))

    def __init__(self, *args, **kwargs):
        super(ArtifactFormNoFile, self).__init__(*args, **kwargs)
        self.fields['categories'].widget = forms.CheckboxSelectMultiple(choices=self.fields['categories'].choices)

    class Meta:
        model = models.Artifact
        fields = ('title', 'notes', 'year', 'tags', 'categories')


class MediaTypeForm(forms.Form):
    mediatype = forms.ChoiceField(label=_(u'Media Type'),initial=_(u'photo'),
                                  required=True, choices=mediachoices)


class PasswordChangeForm(authforms.SetPasswordForm):
    """
    A form that lets a user change his/her password by entering
    their old password.
    """
    old_password = forms.CharField(label=_("Old password"),
                                   widget=forms.PasswordInput)
    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        authed_user = authenticate(username=self.user.username,
                                   password=old_password)
        if authed_user is None:
            raise forms.ValidationError(_("Your old password was entered incorrectly. Please enter it again."))
        return old_password

PasswordChangeForm.base_fields.keyOrder = ['old_password', 'new_password1',
                                           'new_password2']


class PhotoForm(MediaFormBase):
    def __init__(self, *args, **kwargs):
        super(PhotoForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.Photo
        fields = ('title', 'notes', 'year', 'tags', 'image', 'categories')
        widgets = {'notes': forms.Textarea(attrs={'cols': 60, 'rows': 5})}

class PhotoFormNoFile(MediaFormBase):
    notes = forms.CharField(widget = forms.Textarea(attrs={'cols': 60, 'rows': 5}))

    def __init__(self, *args, **kwargs):
        super(PhotoFormNoFile, self).__init__(*args, **kwargs)
        self.fields['categories'].widget = forms.CheckboxSelectMultiple(choices=self.fields['categories'].choices)
        self.fields['notes'].required = False
        self.fields['categories'].required = False

    class Meta:
        model = models.Photo
        fields = ('title', 'notes', 'year', 'tags', 'categories')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = ('url',)


class RegForm(forms.ModelForm):
    class Meta:
        model = authmodels.User
        fields = ('username', 'password', 'first_name', 'last_name', 'email')
        widgets = {'password': forms.PasswordInput(render_value=False)}

    def clean_email(self):
        return clean_email(self)


class UploadForm(forms.Form):
    file_ = forms.FileField(label=_(u'Upload'), required=True)


UploadFormSet = formsets.formset_factory(UploadForm)
UploadFormSet.clean = clean

class UserForm(forms.ModelForm):
    class Meta:
        model = authmodels.User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        return clean_email(self)


class VideoForm(MediaFormBase):
    class Meta:
        model = models.Video
        fields = ('title', 'notes', 'year', 'tags', 'filefield', 'categories')
        widgets = {'notes': forms.Textarea(attrs={'cols': 60, 'rows': 5})}


class VideoFormNoFile(MediaFormBase):
    notes = forms.CharField(widget = forms.Textarea(attrs={'cols': 60, 'rows': 5}))

    def __init__(self, *args, **kwargs):
        super(VideoFormNoFile, self).__init__(*args, **kwargs)
        self.fields['categories'].widget = forms.CheckboxSelectMultiple(choices=self.fields['categories'].choices)


    class Meta:
        model = models.Video
        fields = ('title', 'notes', 'year', 'tags', 'categories')

mediatype_forms = dict(
    photo=PhotoForm,
    artifact=ArtifactForm,
    video=VideoForm,
    )
