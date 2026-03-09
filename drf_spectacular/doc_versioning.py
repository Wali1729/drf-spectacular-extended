import hashlib
import json

from drf_spectacular.models import ApiDocumentationVersion


def compute_endpoint_hashes(schema):
    """
    Walk schema['paths'] and produce a dict mapping 'METHOD:/path/' to a
    SHA-256 hex digest of the canonical JSON for that operation object.
    """
    hashes = {}
    for path, methods in (schema.get('paths') or {}).items():
        for method, operation in methods.items():
            if method.startswith('x-'):
                continue
            key = f'{method.upper()}:{path}'
            canonical = json.dumps(operation, sort_keys=True, default=str)
            hashes[key] = hashlib.sha256(canonical.encode()).hexdigest()
    return hashes


def compute_changes(current_hashes, previous_hashes):
    """
    Compare two endpoint-hash dicts and return a summary of what changed.
    """
    current_keys = set(current_hashes)
    previous_keys = set(previous_hashes)

    new = sorted(current_keys - previous_keys)
    removed = sorted(previous_keys - current_keys)
    modified = sorted(
        key for key in current_keys & previous_keys
        if current_hashes[key] != previous_hashes[key]
    )
    return {'new': new, 'modified': modified, 'removed': removed}


def create_version_snapshot(version, schema, force=False):
    """
    Create a new ApiDocumentationVersion record if the schema has changed
    (or if force=True). Returns (instance, created_bool).

    When the endpoint hashes are identical to the latest stored version
    and force is False, returns (latest_existing, False).
    """
    current_hashes = compute_endpoint_hashes(schema)

    try:
        latest = ApiDocumentationVersion.objects.latest()
    except ApiDocumentationVersion.DoesNotExist:
        latest = None

    if latest and not force:
        if current_hashes == latest.endpoint_hashes:
            return latest, False

    previous_hashes = latest.endpoint_hashes if latest else {}
    changes = compute_changes(current_hashes, previous_hashes)

    doc_version = ApiDocumentationVersion.objects.create(
        version=version,
        schema=schema,
        endpoint_hashes=current_hashes,
        changes_summary=changes,
    )
    return doc_version, True
