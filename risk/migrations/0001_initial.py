# Reconstructed to match the schema actually already deployed (before the
# code/status/full_code additions) — matched by migration NAME, not
# content, so this must reflect what's really in the live database, not
# what's currently in models.py. See 0002 for the additive changes.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Pipeline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='PipelineSegment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_code', models.CharField(max_length=100, unique=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('environmental_data', models.JSONField(blank=True, default=dict)),
                ('inspection_history', models.JSONField(blank=True, default=dict)),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='segments', to='risk.pipeline')),
            ],
        ),
        migrations.CreateModel(
            name='RiskAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('risk_score', models.IntegerField()),
                ('risk_level', models.CharField(max_length=50)),
                ('explanation', models.TextField()),
                ('recommendation', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('segment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_assessments', to='risk.pipelinesegment')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Incident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('incident_type', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('severity', models.CharField(max_length=50)),
                ('segment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='risk.pipelinesegment')),
            ],
        ),
    ]
