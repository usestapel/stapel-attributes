"""Contract test: the FeatureConfig/DTO/DAO discriminator mapping.

Regression coverage for the bug where drf-spectacular's
``PolymorphicProxySerializerExtension`` collapsed all ten feature-type slugs
into a single bogus ``"null"`` mapping entry (see serializers.py's
``_get_proxy_serializer`` for the root-cause writeup: DRF's
``ChoiceField.to_representation`` short-circuits ``None``/``''`` straight
back to ``None`` instead of resolving the field's constant value, so
drf-spectacular's *infer-from-a-list* heuristic produced ``None`` for every
sub-serializer). openapi-typescript then strips ``type`` from generated
call-sites and re-adds a synthetic, wrong one (``IntConfig`` declaring
``type: "IntConfig"`` where the wire sends ``"int"``).

The fix passes an explicit ``{slug: serializer_class}`` dict into
``PolymorphicProxySerializer(serializers=...)``, which drf-spectacular uses
verbatim as the discriminator mapping keys — no inference, no ``None``.
"""

from rest_framework.response import Response
from rest_framework.views import APIView

import pytest

from django.test import override_settings

from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import extend_schema

from stapel_attributes.registry import get_all_type_slugs
from stapel_attributes.serializers import (
    get_feature_config_proxy_serializer,
    get_feature_dao_proxy_serializer,
    get_feature_dto_proxy_serializer,
)

pytestmark = pytest.mark.usefixtures("registry_snapshot")


def _schema_for(proxy_serializer):
    """Render an OpenAPI schema for a single throwaway endpoint returning
    ``proxy_serializer``, and return its component's ``discriminator`` dict.
    """

    from django.urls import path

    with override_settings(
        REST_FRAMEWORK={"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}
    ):
        # extend_schema() reads api_settings.DEFAULT_SCHEMA_CLASS at
        # decoration time, so the view class must be built *inside* the
        # override_settings scope too — not just the generator call.
        class _ProbeView(APIView):
            @extend_schema(responses=proxy_serializer)
            def get(self, request):
                return Response({})

        urlpatterns = [path("probe/", _ProbeView.as_view())]
        generator = SchemaGenerator(patterns=urlpatterns)
        schema = generator.get_schema(request=None, public=True)
    component = schema["components"]["schemas"][proxy_serializer.component_name]
    return component["discriminator"]


class TestDiscriminatorMapping:
    def test_config_mapping_has_all_slugs_no_null(self):
        discriminator = _schema_for(get_feature_config_proxy_serializer())
        mapping = discriminator["mapping"]
        assert "null" not in mapping
        assert None not in mapping
        assert set(mapping) == set(get_all_type_slugs())
        assert len(mapping) == len(get_all_type_slugs())

    def test_dto_mapping_has_all_slugs_no_null(self):
        discriminator = _schema_for(get_feature_dto_proxy_serializer())
        mapping = discriminator["mapping"]
        assert "null" not in mapping
        assert set(mapping) == set(get_all_type_slugs())

    def test_dao_mapping_has_all_slugs_no_null(self):
        discriminator = _schema_for(get_feature_dao_proxy_serializer())
        mapping = discriminator["mapping"]
        assert "null" not in mapping
        assert set(mapping) == set(get_all_type_slugs())

    def test_mapping_values_point_at_the_right_component(self):
        discriminator = _schema_for(get_feature_config_proxy_serializer())
        mapping = discriminator["mapping"]
        assert mapping["int"] == "#/components/schemas/IntConfig"
