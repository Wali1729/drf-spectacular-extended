from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError
from django.utils import translation
from django.utils.module_loading import import_string

from drf_spectacular.doc_versioning import create_version_snapshot
from drf_spectacular.drainage import GENERATOR_STATS
from drf_spectacular.settings import patched_settings, spectacular_settings


class Command(BaseCommand):
    help = dedent("""
        Generate a versioned API documentation snapshot.

        Produces an OpenAPI schema, computes per-endpoint hashes,
        detects changes vs the previous snapshot, and stores the
        result in the database. Skips creation when nothing changed
        unless --force is specified.
    """)

    def add_arguments(self, parser):
        parser.add_argument(
            '--doc-version', dest='doc_version', required=True, type=str,
            help='Version string for this snapshot (e.g. "v1.2.0").',
        )
        parser.add_argument('--urlconf', dest='urlconf', default=None, type=str)
        parser.add_argument('--generator-class', dest='generator_class', default=None, type=str)
        parser.add_argument('--api-version', dest='api_version', default=None, type=str)
        parser.add_argument('--lang', dest='lang', default=None, type=str)
        parser.add_argument('--custom-settings', dest='custom_settings', default=None, type=str)
        parser.add_argument(
            '--force', dest='force', default=False, action='store_true',
            help='Create snapshot even if schema is unchanged.',
        )

    def handle(self, *args, **options):
        if options['generator_class']:
            generator_class = import_string(options['generator_class'])
        else:
            generator_class = spectacular_settings.DEFAULT_GENERATOR_CLASS

        generator = generator_class(
            urlconf=options['urlconf'],
            api_version=options['api_version'],
        )

        if options['custom_settings']:
            custom_settings = import_string(options['custom_settings'])
        else:
            custom_settings = None

        with patched_settings(custom_settings):
            if options['lang']:
                with translation.override(options['lang']):
                    schema = generator.get_schema(request=None, public=True)
            else:
                schema = generator.get_schema(request=None, public=True)

        GENERATOR_STATS.emit_summary()

        version_str = options['doc_version']

        from drf_spectacular.models import ApiDocumentationVersion
        if ApiDocumentationVersion.objects.filter(version=version_str).exists():
            raise CommandError(
                f'Version "{version_str}" already exists. '
                f'Choose a different version string or delete the existing one first.'
            )

        doc_version, created = create_version_snapshot(
            version=version_str,
            schema=schema,
            force=options['force'],
        )

        if created:
            changes = doc_version.changes_summary or {}
            n_new = len(changes.get('new', []))
            n_mod = len(changes.get('modified', []))
            n_rem = len(changes.get('removed', []))
            self.stdout.write(self.style.SUCCESS(
                f'Created documentation snapshot "{version_str}": '
                f'{n_new} new, {n_mod} modified, {n_rem} removed endpoints.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Schema unchanged from latest version "{doc_version.version}". '
                f'Snapshot skipped. Use --force to create anyway.'
            ))
