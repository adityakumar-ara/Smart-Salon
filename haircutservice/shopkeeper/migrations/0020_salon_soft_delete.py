from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopkeeper', '0019_salonfeedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='salon',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='salon',
            name='removed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
