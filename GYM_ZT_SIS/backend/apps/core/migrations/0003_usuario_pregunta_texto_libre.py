from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_usuario_pregunta_respuesta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='pregunta_secreta',
            field=models.CharField(max_length=200, blank=True, default=''),
        ),
    ]
