from bm.signedauth.models import UserKey
from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
import logging

log = logging.getLogger(__name__)

class ExploreForm(forms.Form):
    """A simple form to build a signed url"""
    url = forms.CharField(label=_('URL'), required=True)
    seed = forms.CharField(label=_('Seed (leave blank for for auto)'), required=False)
    user = forms.BooleanField(label=_('Sign as you?'), required=False, initial=True)

    #def __init__(self, *args, **kwargs):
    #    super(ExploreForm, self).__init__(self, *args, **kwargs)
    #    self.signed = ''

    def sign(self, request):
        user = None
        data = self.cleaned_data
        if data.get('user', False):
            user = request.user

        try:
            key = UserKey.objects.get(user=user)
        except UserKey.DoesNotExist:
            key = UserKey(user=user, active=True)
            key.save()

        seed = data.get('seed','')

        if not seed or seed == '':
            seed = None

        url = data['url']

        self.signed = key.sign_url(url, seed=seed)
        self.orig = url

@login_required
def explore(request):
    """A simple view to build and display a signed url"""

    if request.method == "POST":
        data = request.POST.copy()
        form = ExploreForm(data)
        if form.is_valid():
            form.sign(request)
    else:
        form = ExploreForm()

    ctx = RequestContext(request, {'form' : form})
    return render_to_response('signedauth/explore/explore.html', ctx)
