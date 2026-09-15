"""
Adds the fields introduced to match the frontend's API contract:
Pipeline.code, PipelineSegment.status, PipelineSegment uniqueness
scoped per-pipeline instead of globally, and Incident.severity made
optional (+ deduped by type/date).

Pipeline.code is unique and required, so it can't just be added with a
single shared default if more than one Pipeline row already exists —
that would violate the unique constraint. Instead: add it nullable,
backfill each existing row with a guaranteed-unique placeholder derived
from its own id, then tighten it to unique+required.
"""
from django.db import migrations, models


def backfill_pipeline_codes(apps, schema_editor):
    Pipeline = apps.get_model('risk', 'Pipeline')
    for pipeline in Pipeline.objects.filter(code__isnull=True):
        pipeline.code = f'PIPE-{pipeline.pk}'
        pipeline.save(update_fields=['code'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0001_initial'),
    ]

    operations = [
        # --- Pipeline.code: add nullable, backfill, then tighten ---
        migrations.AddField(
            model_name='pipeline',
            name='code',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.RunPython(backfill_pipeline_codes, noop_reverse),
        migrations.AlterField(
            model_name='pipeline',
            name='code',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='status',
            field=models.CharField(default='active', max_length=50),
        ),

        # --- PipelineSegment.status + uniqueness scoped to pipeline ---
        migrations.AddField(
            model_name='pipelinesegment',
            name='status',
            field=models.CharField(default='Active', max_length=100),
        ),
        migrations.AlterField(
            model_name='pipelinesegment',
            name='segment_code',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='pipelinesegment',
            unique_together={('pipeline', 'segment_code')},
        ),

        # --- Incident.severity optional + dedupe by type/date ---
        migrations.AlterField(
            model_name='incident',
            name='severity',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='incident',
            unique_together={('segment', 'incident_type', 'date')},
        ),
    ]
