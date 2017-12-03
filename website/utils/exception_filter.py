import logging

from django.views.debug import (SafeExceptionReporterFilter,
                                CLEANSED_SUBSTITUTE)


logger = logging.getLogger(__name__)


class ThaliaSafeExceptionReporterFilter(SafeExceptionReporterFilter):
    """Filter additional variables from tracebacks"""

    def get_traceback_frame_variables(self, request, tb_frame):
        """Filter traceback frame variables"""
        local_vars = super().get_traceback_frame_variables(request, tb_frame)

        if self.is_active(request):
            for name, val in local_vars:
                if name == 'request':
                    try:
                        val.COOKIES = {'cookies have been cleaned': True}
                        val.META['HTTP_COOKIE'] = CLEANSED_SUBSTITUTE
                        val.META['HTTP_AUTHORIZATION'] = CLEANSED_SUBSTITUTE
                    except (AttributeError, IndexError):
                        logger.exception("Somehow cleaning the request failed")

        return local_vars