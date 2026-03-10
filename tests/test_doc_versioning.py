import json
from unittest import mock

import pytest
from django.core import management
from django.core.management import CommandError
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient

from drf_spectacular_extended.doc_versioning import (
    compute_changes,
    compute_endpoint_hashes,
    create_version_snapshot,
)
from drf_spectacular_extended.models import ApiDocumentationVersion
from drf_spectacular_extended.types import OpenApiTypes
from drf_spectacular_extended.utils import extend_schema
from drf_spectacular_extended.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularVersionDetailView,
    SpectacularVersionListView,
)


SAMPLE_SCHEMA = {
    'openapi': '3.0.3',
    'info': {'title': 'Test', 'version': '1.0'},
    'paths': {
        '/api/users/': {
            'get': {
                'operationId': 'users_list',
                'responses': {'200': {'description': 'OK'}},
            },
            'post': {
                'operationId': 'users_create',
                'requestBody': {'content': {'application/json': {}}},
                'responses': {'201': {'description': 'Created'}},
            },
        },
        '/api/items/': {
            'get': {
                'operationId': 'items_list',
                'responses': {'200': {'description': 'OK'}},
            },
        },
    },
    'components': {},
}


# ---------------------------------------------------------------------------
# Unit tests for hashing and diffing
# ---------------------------------------------------------------------------

class TestComputeEndpointHashes:
    def test_basic_hashing(self):
        hashes = compute_endpoint_hashes(SAMPLE_SCHEMA)
        assert set(hashes.keys()) == {
            'GET:/api/users/',
            'POST:/api/users/',
            'GET:/api/items/',
        }
        for v in hashes.values():
            assert len(v) == 64  # SHA-256 hex digest

    def test_deterministic(self):
        h1 = compute_endpoint_hashes(SAMPLE_SCHEMA)
        h2 = compute_endpoint_hashes(SAMPLE_SCHEMA)
        assert h1 == h2

    def test_empty_paths(self):
        schema = {**SAMPLE_SCHEMA, 'paths': {}}
        assert compute_endpoint_hashes(schema) == {}

    def test_skips_extensions(self):
        schema = {
            **SAMPLE_SCHEMA,
            'paths': {
                '/x/': {
                    'get': {'operationId': 'x'},
                    'x-custom': 'ignored',
                },
            },
        }
        hashes = compute_endpoint_hashes(schema)
        assert 'X-CUSTOM:/x/' not in hashes
        assert 'GET:/x/' in hashes


class TestComputeChanges:
    def test_all_new(self):
        changes = compute_changes({'GET:/a/': 'h1'}, {})
        assert changes == {'new': ['GET:/a/'], 'modified': [], 'removed': []}

    def test_all_removed(self):
        changes = compute_changes({}, {'GET:/a/': 'h1'})
        assert changes == {'new': [], 'modified': [], 'removed': ['GET:/a/']}

    def test_modified(self):
        changes = compute_changes({'GET:/a/': 'h2'}, {'GET:/a/': 'h1'})
        assert changes == {'new': [], 'modified': ['GET:/a/'], 'removed': []}

    def test_unchanged(self):
        changes = compute_changes({'GET:/a/': 'h1'}, {'GET:/a/': 'h1'})
        assert changes == {'new': [], 'modified': [], 'removed': []}

    def test_mixed(self):
        current = {'GET:/a/': 'h1', 'POST:/b/': 'h2', 'GET:/c/': 'changed'}
        previous = {'GET:/a/': 'h1', 'GET:/c/': 'old', 'DELETE:/d/': 'h3'}
        changes = compute_changes(current, previous)
        assert changes['new'] == ['POST:/b/']
        assert changes['modified'] == ['GET:/c/']
        assert changes['removed'] == ['DELETE:/d/']


# ---------------------------------------------------------------------------
# Database integration tests for create_version_snapshot
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateVersionSnapshot:
    def test_first_snapshot(self):
        doc, created = create_version_snapshot('v1.0', SAMPLE_SCHEMA)
        assert created is True
        assert doc.version == 'v1.0'
        assert doc.endpoint_hashes
        assert doc.changes_summary['new']
        assert doc.changes_summary['modified'] == []
        assert doc.changes_summary['removed'] == []

    def test_skip_unchanged(self):
        create_version_snapshot('v1.0', SAMPLE_SCHEMA)
        existing, created = create_version_snapshot('v1.1', SAMPLE_SCHEMA)
        assert created is False
        assert existing.version == 'v1.0'

    def test_force_creates_even_if_unchanged(self):
        create_version_snapshot('v1.0', SAMPLE_SCHEMA)
        doc, created = create_version_snapshot('v1.1', SAMPLE_SCHEMA, force=True)
        assert created is True
        assert doc.version == 'v1.1'

    def test_detects_changes(self):
        create_version_snapshot('v1.0', SAMPLE_SCHEMA)
        modified_schema = json.loads(json.dumps(SAMPLE_SCHEMA))
        modified_schema['paths']['/api/users/']['get']['responses']['200']['description'] = 'Modified'
        modified_schema['paths']['/api/new/'] = {
            'get': {'operationId': 'new_list', 'responses': {'200': {'description': 'OK'}}},
        }
        del modified_schema['paths']['/api/items/']

        doc, created = create_version_snapshot('v2.0', modified_schema)
        assert created is True
        assert 'GET:/api/new/' in doc.changes_summary['new']
        assert 'GET:/api/users/' in doc.changes_summary['modified']
        assert 'GET:/api/items/' in doc.changes_summary['removed']


# ---------------------------------------------------------------------------
# Management command tests
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.FLOAT)
@api_view(http_method_names=['GET'])
def pi(request):
    return Response(3.1415)


urlpatterns = [
    path('api/pi/', pi),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/versions/', SpectacularVersionListView.as_view(), name='schema-versions'),
    path(
        'api/schema/versions/<str:version>/',
        SpectacularVersionDetailView.as_view(),
        name='schema-version-detail',
    ),
    path(
        'api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]


@pytest.mark.django_db
@pytest.mark.urls(__name__)
class TestGenerateDocVersionCommand:
    def test_creates_first_version(self, capsys, clear_generator_settings):
        management.call_command('generate_doc_version', '--doc-version=v1.0')
        out = capsys.readouterr().out
        assert 'Created documentation snapshot "v1.0"' in out
        assert ApiDocumentationVersion.objects.filter(version='v1.0').exists()

    def test_skips_unchanged(self, capsys, clear_generator_settings):
        management.call_command('generate_doc_version', '--doc-version=v1.0')
        management.call_command('generate_doc_version', '--doc-version=v1.1')
        out = capsys.readouterr().out
        assert 'Schema unchanged' in out
        assert not ApiDocumentationVersion.objects.filter(version='v1.1').exists()

    def test_force_creates(self, capsys, clear_generator_settings):
        management.call_command('generate_doc_version', '--doc-version=v1.0')
        management.call_command('generate_doc_version', '--doc-version=v1.1', '--force')
        assert ApiDocumentationVersion.objects.filter(version='v1.1').exists()

    def test_duplicate_version_raises(self, capsys, clear_generator_settings):
        management.call_command('generate_doc_version', '--doc-version=v1.0')
        with pytest.raises(CommandError, match='already exists'):
            management.call_command('generate_doc_version', '--doc-version=v1.0')


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.urls(__name__)
class TestVersionListView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        ApiDocumentationVersion.objects.create(
            version='v1.0',
            schema=SAMPLE_SCHEMA,
            endpoint_hashes={'GET:/api/users/': 'abc'},
            changes_summary={'new': ['GET:/api/users/'], 'modified': [], 'removed': []},
        )

    def test_list_returns_versions(self):
        response = APIClient().get('/api/schema/versions/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]['version'] == 'v1.0'
        assert data[0]['changes_summary']['new'] == ['GET:/api/users/']


@pytest.mark.django_db
@pytest.mark.urls(__name__)
class TestVersionDetailView:
    @pytest.fixture(autouse=True)
    def _setup(self):
        ApiDocumentationVersion.objects.create(
            version='v1.0',
            schema=SAMPLE_SCHEMA,
            endpoint_hashes={'GET:/api/users/': 'abc'},
            changes_summary={'new': ['GET:/api/users/'], 'modified': [], 'removed': []},
        )

    def test_detail_returns_version(self):
        response = APIClient().get('/api/schema/versions/v1.0/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['version'] == 'v1.0'

    def test_detail_404_for_missing(self):
        response = APIClient().get('/api/schema/versions/v99.0/')
        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.urls(__name__)
class TestVersionedSchemaServing:
    @mock.patch('drf_spectacular_extended.settings.spectacular_settings.VERSIONED_DOCS_ENABLED', True)
    @mock.patch('drf_spectacular_extended.settings.spectacular_settings.VERSIONED_DOCS_SERVE_LATEST', True)
    def test_serves_stored_schema(self):
        stored_schema = {**SAMPLE_SCHEMA, 'info': {'title': 'Stored', 'version': '1.0'}}
        ApiDocumentationVersion.objects.create(
            version='v1.0',
            schema=stored_schema,
            endpoint_hashes={'GET:/api/users/': 'abc'},
        )
        response = APIClient().get('/api/schema/', HTTP_ACCEPT='application/json')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['info']['title'] == 'Stored'

    @mock.patch('drf_spectacular_extended.settings.spectacular_settings.VERSIONED_DOCS_ENABLED', True)
    @mock.patch('drf_spectacular_extended.settings.spectacular_settings.VERSIONED_DOCS_SERVE_LATEST', True)
    def test_serves_specific_version(self):
        ApiDocumentationVersion.objects.create(
            version='v1.0', schema={**SAMPLE_SCHEMA, 'info': {'title': 'V1', 'version': '1'}},
            endpoint_hashes={},
        )
        ApiDocumentationVersion.objects.create(
            version='v2.0', schema={**SAMPLE_SCHEMA, 'info': {'title': 'V2', 'version': '2'}},
            endpoint_hashes={},
        )
        response = APIClient().get(
            '/api/schema/?doc_version=v1.0', HTTP_ACCEPT='application/json',
        )
        data = json.loads(response.content)
        assert data['info']['title'] == 'V1'

    @mock.patch('drf_spectacular_extended.settings.spectacular_settings.VERSIONED_DOCS_ENABLED', False)
    def test_falls_back_to_live_generation(self):
        response = APIClient().get('/api/schema/', HTTP_ACCEPT='application/json')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'paths' in data
