from django.db import models


class ApiDocumentationVersion(models.Model):
    version = models.CharField(max_length=100, unique=True, db_index=True)
    schema = models.JSONField(help_text="Full OpenAPI schema JSON")
    endpoint_hashes = models.JSONField(
        default=dict,
        help_text="Mapping of 'METHOD:/path/' to hash of operation schema",
    )
    changes_summary = models.JSONField(
        null=True,
        blank=True,
        help_text="Diff vs previous version: {new: [...], modified: [...], removed: [...]}",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'

    def __str__(self):
        return f"API Docs {self.version} ({self.created_at})"
