import functools

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import path
from iommi import Part

from radio2playlist.models import (
    Artist,
    Playlist,
    Show,
    Station,
    Track,
)

_url_decoding_models = []


def register_models_for_url_decoding(*models):
    _url_decoding_models.extend(models)


def decode_url(*, op='edit'):

    def decode_url_factory(f):
        @functools.wraps(f)
        def decode_url_wrapper(request, **kwargs):
            decoded_kwargs = {}
            for model in _url_decoding_models:
                model_name = model.__name__.lower().replace(' ', '_')
                pk_key = f'{model_name}_pk'
                name_key = f'{model_name}_name'

                if pk_key in kwargs:
                    # view(foo_pk=123)
                    lookup = dict(pk=kwargs.pop(pk_key))
                elif name_key in kwargs:
                    # view(foo_name='foo')
                    lookup = dict(name=kwargs.pop(name_key))
                elif model_name in kwargs:
                    # view(foo=foo)
                    decoded_kwargs[model_name] = kwargs.pop(model_name)
                    continue
                else:
                    continue

                dependencies = getattr(model, 'decode_url_dependencies', lambda: [])()
                for dependency in dependencies:
                    lookup[dependency] = decoded_kwargs[dependency]

                obj = get_object_or_404(model, **lookup)
                decoded_kwargs[model_name] = obj

                if not obj.has_permission(user=request.user, request=request, op=op):
                    return HttpResponseForbidden(f'Access denied for {obj.__class__.__name__} {obj.pk}, operation {op}')

            request.url_params = decoded_kwargs

            return f(request=request, **decoded_kwargs, **kwargs)

        return decode_url_wrapper

    return decode_url_factory


def decoded_path(p, view, *, op='edit'):
    if isinstance(view, Part):
        view = view.as_view()
    return path(p, decode_url(op=op)(view))


register_models_for_url_decoding(
    Station,
    Show,
    Artist,
    Track,
    Playlist,
)
