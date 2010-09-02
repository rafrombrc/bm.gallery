from bm.gallery import models
from bm.gallery import utils


class TemplateAPI(object):
    def __init__(self, request):
        self.request = request

    def year_choices(self):
        return utils.year_choices()

    def mediatype_choices(self):
        return [(key, value['title']) for key, value
                in models.mediatype_map.items()]

    def category_choices(self):
        return utils.category_choices()

    def status_choices(self):
        return models.statuses

def template_api(request):
    api = TemplateAPI(request)
    return {'api': api}
