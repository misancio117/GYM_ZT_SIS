from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='pregunta_secreta',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('mascota', '¿Cuál es el nombre de tu mascota?'),
                    ('ciudad', '¿En qué ciudad naciste?'),
                    ('comida', '¿Cuál es tu comida favorita?'),
                    ('amigo', '¿Cuál es el nombre de tu mejor amigo/a?'),
                    ('madre', '¿Cuál es el primer apellido de tu madre?'),
                    ('escuela', '¿Cómo se llamaba tu escuela primaria?'),
                ],
                blank=True,
                default='',
            ),
        ),
        migrations.AddField(
            model_name='usuario',
            name='respuesta_secreta',
            field=models.CharField(max_length=128, blank=True, default=''),
        ),
    ]
