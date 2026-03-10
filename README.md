# drf-spectacular (extended)

[![build-status](https://github.com/tfranzel/drf-spectacular/actions/workflows/ci.yml/badge.svg)](https://github.com/tfranzel/drf-spectacular/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tfranzel/drf-spectacular/branch/master/graph/badge.svg)](https://codecov.io/gh/tfranzel/drf-spectacular)
[![docs](https://readthedocs.org/projects/drf-spectacular/badge/)](https://drf-spectacular.readthedocs.io/)
[![pypi-version](https://img.shields.io/pypi/v/drf-spectacular.svg)](https://pypi.org/project/drf-spectacular/)
[![pypi-dl](https://img.shields.io/pypi/dm/drf-spectacular)](https://pypi.org/project/drf-spectacular/)

Sane and flexible [OpenAPI](https://swagger.io/) ([3.0.3](https://spec.openapis.org/oas/v3.0.3) & [3.1](https://spec.openapis.org/oas/v3.1.0)) schema generation for [Django REST framework](https://www.django-rest-framework.org/).

This project has 3 goals:

1. Extract as much schema information from DRF as possible.
2. Provide flexibility to make the schema usable in the real world (not only toy examples).
3. Generate a schema that works well with the most popular client generators.

The code is a heavily modified fork of the
[DRF OpenAPI generator](https://github.com/encode/django-rest-framework/blob/master/rest_framework/schemas/openapi.py/),
which is/was lacking all of the below listed features.

## Features

- Serializers modelled as components (arbitrary nesting and recursion supported).
- [`@extend_schema`](https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular_extended.html#drf_spectacular_extended.utils.extend_schema) decorator for customization of APIView, Viewsets, function-based views, and `@action`
  - additional parameters
  - request/response serializer override (with status codes)
  - polymorphic responses either manually with `PolymorphicProxySerializer` helper or via `rest_polymorphic`'s PolymorphicSerializer)
  - ... and more customization options
- Authentication support (DRF natives included, easily extendable)
- Custom serializer class support (easily extendable)
- `SerializerMethodField()` type via type hinting or `@extend_schema_field`
- i18n support
- Tags extraction
- Request/response/parameter examples
- Description extraction from `docstrings`
- Vendor specification extensions (`x-*`) in info, operations, parameters, components, and security schemes
- Sane fallbacks
- Sane `operation_id` naming (based on path)
- Schema serving with `SpectacularAPIView` (Redoc and Swagger-UI views are also available)
- Optional input/output serializer component split
- Callback operations
- OpenAPI 3.1 support (via setting `OAS_VERSION`)
- Included support for:
  - [`django-polymorphic`](https://github.com/django-polymorphic/django-polymorphic) / [`django-rest-polymorphic`](https://github.com/apirobot/django-rest-polymorphic)
  - [`SimpleJWT`](https://github.com/jazzband/djangorestframework-simplejwt)
  - [`DjangoOAuthToolkit`](https://github.com/jazzband/django-oauth-toolkit)
  - [`djangorestframework-jwt`](https://github.com/jpadilla/django-rest-framework-jwt) (tested fork [`drf-jwt`](https://github.com/Styria-Digital/django-rest-framework-jwt))
  - [`dj-rest-auth`](https://github.com/iMerica/dj-rest-auth) (maintained fork of [`django-rest-auth`](https://github.com/Tivix/django-rest-auth))
  - [`djangorestframework-camel-case`](https://github.com/vbabiy/djangorestframework-camel-case) (via postprocessing hook `camelize_serializer_fields`)
  - [`django-filter`](https://github.com/carltongibson/django-filter)
  - [`drf-nested-routers`](https://github.com/alanjds/drf-nested-routers)
  - [`djangorestframework-recursive`](https://github.com/heywbj/django-rest-framework-recursive)
  - [`djangorestframework-dataclasses`](https://github.com/oxan/djangorestframework-dataclasses)
  - [`django-rest-framework-gis`](https://github.com/openwisp/django-rest-framework-gis)
  - [`Pydantic` (>=2.0)](https://github.com/pydantic/pydantic)

For more information visit the [documentation](https://drf-spectacular.readthedocs.io/).

This repository is an extended fork of `drf-spectacular` that is published on PyPI as
`drf_spectacular_extended`. The Python import path and Django app name remain
`drf_spectacular_extended`.

## License

Provided by [T. Franzel](https://github.com/tfranzel). [Licensed under 3-Clause BSD](https://github.com/tfranzel/drf-spectacular/blob/master/LICENSE).

## Requirements

- Python >= 3.7
- Django (2.2, 3.2, 4.0, 4.1, 4.2, 5.0, 5.1, 5.2)
- Django REST Framework (3.10.3, 3.11, 3.12, 3.13, 3.14, 3.15)

## Installation

Install the extended fork using `pip`...

```bash
pip install drf_spectacular_extended
```

then add drf-spectacular to installed apps in `settings.py`:

```python
INSTALLED_APPS = [
    # ALL YOUR APPS
    'drf_spectacular_extended',
]
```

and finally register our spectacular `AutoSchema` with DRF:

```python
REST_FRAMEWORK = {
    # YOUR SETTINGS
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular_extended.openapi.AutoSchema',
}
```

drf-spectacular ships with sane [default settings](https://drf-spectacular.readthedocs.io/en/latest/settings.html)
that should work reasonably well out of the box. It is not necessary to
specify any settings, but we recommend to specify at least some metadata.

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Project API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}
```

### Self-contained UI installation

Certain environments have no direct access to the internet and as such are unable
to retrieve Swagger UI or Redoc from CDNs. [`drf-spectacular-sidecar`](https://github.com/tfranzel/drf-spectacular-sidecar) provides
these static files as a separate optional package. Usage is as follows:

```bash
pip install drf-spectacular[sidecar]
```

```python
INSTALLED_APPS = [
    # ALL YOUR APPS
    'drf_spectacular_extended',
    'drf_spectacular_extended_sidecar',  # required for Django collectstatic discovery
]
SPECTACULAR_SETTINGS = {
    'SWAGGER_UI_DIST': 'SIDECAR',  # shorthand to use the sidecar instead
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    # OTHER SETTINGS
}
```

### Release management

*drf-spectacular* deliberately stays below version *1.x.x* to signal that every
new version may potentially break you. For production we strongly recommend pinning the
version and inspecting a schema diff on update.

With that said, we aim to be extremely defensive w.r.t. breaking API changes. However,
we also acknowledge the fact that even slight schema changes may break your toolchain,
as any existing bug may somehow also be used as a feature.

We define version increments with the following semantics. *y-stream* increments may contain
potentially breaking changes to both API and schema. *z-stream* increments will never break the
API and may only contain schema changes that should have a low chance of breaking you.

## Take it for a spin

Generate your schema with the CLI:

```bash
./manage.py spectacular --color --file schema.yml
docker run -p 8080:8080 -e SWAGGER_JSON=/schema.yml -v ${PWD}/schema.yml:/schema.yml swaggerapi/swagger-ui
```

If you also want to validate your schema add the `--validate` flag. Or serve your schema directly
from your API. We also provide convenience wrappers for `swagger-ui` or `redoc`.

```python
from drf_spectacular_extended.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # YOUR PATTERNS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

### Versioned API documentation (extended)

The extended fork adds first-class support for **versioned documentation snapshots**
with per-endpoint change tracking and an enhanced Swagger UI.

Enable versioned docs in your Django settings:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Your Project API',
    'DESCRIPTION': 'Your project description',
    'VERSION': '1.0.0',
    # enable the extended versioning features
    'VERSIONED_DOCS_ENABLED': True,
    # when True, the schema endpoint serves the latest stored snapshot
    'VERSIONED_DOCS_SERVE_LATEST': True,
}
```

Generate and store a snapshot of your OpenAPI schema with the management command:

```bash
./manage.py generate_doc_version --doc-version=1.0.0
```

This will:

- generate the schema using your configured generator and URLconf
- compute a stable hash per endpoint (`METHOD:/path/`)
- compare against the previous snapshot
- store the full schema plus a summary of **new**, **modified** and **removed** endpoints

You can repeat this whenever your API changes, e.g. during releases:

```bash
./manage.py generate_doc_version --doc-version=1.1.0
```

To expose the stored versions and their change summaries over HTTP, wire up the
additional views:

```python
from drf_spectacular_extended.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularVersionListView,
    SpectacularVersionDetailView,
)

urlpatterns = [
    # schema + UIs as before
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # extended versioning API
    path('api/schema/versions/', SpectacularVersionListView.as_view(), name='schema-versions'),
    path(
        'api/schema/versions/<str:version>/',
        SpectacularVersionDetailView.as_view(),
        name='schema-version-detail',
    ),
]
```

When `VERSIONED_DOCS_ENABLED` is set, the Swagger UI gains:

- a **version selector** to switch between stored snapshots (via `doc_version` parameter)
- a **Changes** tab showing new / modified / removed endpoints for the selected version
- a **Releases** tab listing all versions with change counts

This allows you to see at a glance what changed between documentation releases while
still serving a full OpenAPI document to client generators and other tooling.

## Usage

*drf-spectacular* works pretty well out of the box. You might also want to set some metadata for your API.
Just create a `SPECTACULAR_SETTINGS` dictionary in your `settings.py` and override the defaults.
Have a look at the [available settings](https://drf-spectacular.readthedocs.io/en/latest/settings.html).

The toy examples do not cover your cases? No problem, you can heavily customize how your schema will be rendered.

### Customization by using `@extend_schema`

Most customization cases should be covered by the `extend_schema` decorator. We usually get
pretty far with specifying `OpenApiParameter` and splitting request/response serializers, but
the sky is the limit.

```python
from drf_spectacular_extended.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular_extended.types import OpenApiTypes

class AlbumViewset(viewset.ModelViewset):
    serializer_class = AlbumSerializer

    @extend_schema(
        request=AlbumCreationSerializer,
        responses={201: AlbumSerializer},
    )
    def create(self, request):
        # your non-standard behaviour
        return super().create(request)

    @extend_schema(
        # extra parameters added to the schema
        parameters=[
            OpenApiParameter(name='artist', description='Filter by artist', required=False, type=str),
            OpenApiParameter(
                name='release',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter by release date',
                examples=[
                    OpenApiExample(
                        'Example 1',
                        summary='short optional summary',
                        description='longer description',
                        value='1993-08-23'
                    ),
                    ...
                ],
            ),
        ],
        # override default docstring extraction
        description='More descriptive text',
        # provide Authentication class that deviates from the views default
        auth=None,
        # change the auto-generated operation name
        operation_id=None,
        # or even completely override what AutoSchema would generate. Provide raw Open API spec as Dict.
        operation=None,
        # attach request/response examples to the operation.
        examples=[
            OpenApiExample(
                'Example 1',
                description='longer description',
                value=...
            ),
            ...
        ],
    )
    def list(self, request):
        # your non-standard behaviour
        return super().list(request)

    @extend_schema(
        request=AlbumLikeSerializer,
        responses={204: None},
        methods=["POST"]
    )
    @extend_schema(description='Override a specific method', methods=["GET"])
    @action(detail=True, methods=['post', 'get'])
    def set_password(self, request, pk=None):
        # your action behaviour
        ...
```

### More customization

Still not satisfied? You want more! We still got you covered.
Visit [customization](https://drf-spectacular.readthedocs.io/en/latest/customization.html) for more information.

## Testing

Install testing requirements.

```bash
pip install -r requirements.txt
```

Run with `runtests`:

```bash
./runtests.py
```

You can also use the excellent [`tox`](https://tox.wiki/) testing tool to run the tests
against all supported versions of Python and Django. Install tox
globally, and then simply run:

```bash
tox
```

## Release branches and CI/CD

Releases for this package are driven by two protected branches:

- `release`: merges into this branch run the full CI workflow and then publish the package to PyPI.
- `test_release`: merges into this branch run the same CI workflow and publish the package to TestPyPI.

Both branches are intended to be **protected** in GitHub:

- direct pushes should be disallowed
- changes should land only via pull requests
- the `Required tests passed` check from `ci.yml` should be required before merging

