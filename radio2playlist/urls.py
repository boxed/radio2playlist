from django.urls import include
from iommi import Table
from iommi.admin import Admin
from .path import decoded_path

from radio2playlist.models import (
    Show,
    Station,
)

urlpatterns = [
    decoded_path('', Table(
        auto__model=Station,
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
    ).as_view()),
    decoded_path('stations/<int:station_pk>/', Table(
        auto__model=Show,
        rows=lambda request, **_: request.url_params['station'].shows.all(),
        columns__name__cell__url=lambda row, **_: row.get_absolute_url(),
    ).as_view()),

    decoded_path('admin/', include(Admin.urls())),
]
