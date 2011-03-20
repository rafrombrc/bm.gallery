from piston.handler import BaseHandler

class EchoHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        echo = request.GET.get('echo','---')
        return {
            'echo' : echo,
            'data_length' : len(echo)
            }

