"""
Customize logging for  Project teaching_helper
"""

import os
import functools
import inspect
import logging
import logging.config
import typing

from rest_framework import status
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import HttpResponse, render

from teaching_helper import gdata

__all__ = [r'get_logger', r'APIViewCatchException']

current_dir = os.path.abspath(os.path.dirname(__file__))
log_conf_path = os.path.join(current_dir, 'logging.ini')

logging.config.fileConfig(log_conf_path)


# functions


def get_logger(name):
    return logging.getLogger(name)


def _get_local_self_ins():
    """Get `self` instance in class object method
    """
    frame = inspect.currentframe().f_back.f_back
    _, _, _, init_method_locals = inspect.getargvalues(frame)

    return init_method_locals.get('self', None)


# classes


class BaseDecorator(object):

    def __init__(self, obj, logger, decor_methods: typing.List = None):
        """
        :param obj:
        :param logger:
        :param decor_methods: decorated classes set
            * default -> gdata.REST_HTTP_METHODS
        """
        self.obj = obj
        self.logger = logger
        self.decor_methods = decor_methods

        self._set_default()

    def decorate(self):
        for name, method in self._iter():
            self._call(name, method)

    def _iter(self):
        for _f_name in dir(self.obj):
            if _f_name.lower() in self.decor_methods:
                yield _f_name, getattr(self.obj, _f_name)

    def _set_default(self):
        """init member variable which is None

        you must assign a default value to member variable of `self` which is None
        """
        raise NotImplementedError('_set_default must be implemented by subclass')

    def _call(self, name, method):
        """method substitution
        """
        raise NotImplementedError('_set_default must be implemented by subclass')


class APIViewCatchException(BaseDecorator):
    """This class automatically catches exceptions under the specified set of methods

    process: by method substitution

    example:
        you want to initialize a class named `BookInfoView`,
        so that, you can use this class as follows:

        ```
        >>> def __init__(self, **kwargs):
        >>>     APIViewCatchException().decorate()
        ```
    """

    def _set_default(self):
        if not self.obj:
            self.obj = _get_local_self_ins()
        if not self.logger:
            self.logger = get_logger(__name__)
        if not self.decor_methods:
            self.decor_methods = [_f.lower() for _f in gdata.REST_HTTP_METHODS]

    def _call(self, func_name, func):
        """execute method under protection
        """

        @functools.wraps(func)
        def new_method(*args, **kwargs):
            try:
                _response = func(*args, **kwargs)
                if not isinstance(_response, (Response, render, HttpResponse, JsonResponse)):
                    raise Exception('内部异常，响应类型错误.')
                return _response
            except Exception as e:
                self.logger.error(e, exc_info=True)
                return Response(data=e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        setattr(self.obj, func_name, new_method)


# 当方法内发生异常时，返回 value
def convert_exception_to_value(value):
    def _real_decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kv):
            try:
                return fn(*args, **kv)
            except Exception as e:
                logging.getLogger(fn.__module__).error(
                    r'{fn_name} raise Exception need convert to {value} :{e}'.format(
                        fn_name=fn.__qualname__, e=e, value=value), exc_info=True)
                return value

        return wrapper

    return _real_decorator
