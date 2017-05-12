# Original version taken from http://www.djangosnippets.org/snippets/186/
# Original author: udfalkso
# Modified by: Shwagroo Team, Gun.io, TriOptima

from io import StringIO
import cProfile
import os
import subprocess
from tempfile import NamedTemporaryFile

from django.conf import settings

MEDIA_PREFIXES = ['static/']

HIGHLIGHT_KEYWORD = 'great_apis'


class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.

    - Add the "prof" key to query string by appending ?prof (or &prof=) and you'll see the profiling results in your browser.
    - Add both "prof" and "graph" to the querystring to get a graph of the profiling data.

    Based on: https://gun.io/blog/fast-as-fuck-django-part-1-using-a-profiler/
    """
    def __init__(self):
        self.prof = None

    def process_request(self, request):
        # Disable profiling early on /media requests since touching request.user will add a
        # "Vary: Cookie" header to the response.

        request.profiler_disabled = False
        for prefix in MEDIA_PREFIXES:
            if request.path.startswith(prefix):
                request.profiler_disabled = True
                return

        if (settings.DEBUG or request.user.is_staff) and 'prof' in request.GET:
            self.prof = cProfile.Profile()
            self.prof.enable()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not request.profiler_disabled and (settings.DEBUG or request.user.is_staff) and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if not getattr(request, 'profiler_disabled', True) and (settings.DEBUG or (hasattr(request, 'user') and request.user.is_staff)) and 'prof' in request.GET:

            self.prof.disable()

            import pstats
            s = StringIO.StringIO()
            ps = pstats.Stats(self.prof, stream=s).sort_stats('cumulative')
            ps.print_stats()
            stats_str = s.getvalue()

            if 'graph' in request.GET:

                with NamedTemporaryFile() as stats_dump:
                    ps.stream = stats_dump
                    ps.dump_stats(stats_dump.name)
                    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'env')
                    gprof2dot_path = os.path.join(env_path, 'bin', 'gprof2dot')
                    gprof2dot = subprocess.Popen((os.path.join(env_path, 'bin', 'python'), gprof2dot_path, '-f', 'pstats', stats_dump.name), stdout=subprocess.PIPE)
                    response['Content-Type'] = 'image/svg+xml'

                    if os.path.exists('/usr/bin/dot'):
                        response.content = subprocess.check_output(('/usr/bin/dot', '-Tsvg'), stdin=gprof2dot.stdout)
                    elif os.path.exists('/usr/local/bin/dot'):
                        response.content = subprocess.check_output(('/usr/local/bin/dot', '-Tsvg'), stdin=gprof2dot.stdout)
                    else:
                        response['Content-Type'] = 'text/plain'
                        response['Content-Disposition'] = "attachment; filename=gprof2dot-graph.txt"
                        response.content = subprocess.check_output('tee', stdin=gprof2dot.stdout)
            else:
                if response and response.content and stats_str:
                    response.content = stats_str

                limit = 80
                result = []
                for line in response.content.split("\n")[:limit]:
                    line = line.replace(' ', '&nbsp;')
                    result.append('<b>%s</b>' % line if HIGHLIGHT_KEYWORD in line else line)

                response.content = '<div style="font-family: monospace; white-space: nowrap">%s</div' % "<br />\n".join(
                    result)
                response['Content-Type'] = 'text/html'

        return response
