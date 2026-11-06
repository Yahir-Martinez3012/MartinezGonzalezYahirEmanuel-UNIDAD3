import django.db.models.deletion
from django.db import migrations, models


def copiar_cv_existentes(apps, schema_editor):
    """Pasa los CV guardados como archivos a la base de datos (si el archivo ya no existe, se omite)."""
    Perfil = apps.get_model('estudiantes', 'PerfilEstudiante')
    ArchivoCV = apps.get_model('estudiantes', 'ArchivoCV')
    for perfil in Perfil.objects.exclude(cv=''):
        try:
            with perfil.cv.open('rb') as f:
                contenido = f.read()
        except (FileNotFoundError, ValueError, OSError):
            continue
        nombre = (perfil.cv.name.rsplit('/', 1)[-1] or 'cv.pdf')[:150]
        ArchivoCV.objects.update_or_create(perfil=perfil, defaults={'contenido': contenido, 'nombre': nombre})
        perfil.cv_nombre = nombre
        perfil.save(update_fields=['cv_nombre'])


class Migration(migrations.Migration):

    dependencies = [
        ('estudiantes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilestudiante', name='cv_nombre',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='perfilestudiante', name='cv_subido',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='ArchivoCV',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.BinaryField()),
                ('nombre', models.CharField(max_length=150)),
                ('subido', models.DateTimeField(auto_now=True)),
                ('perfil', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                related_name='archivo_cv', to='estudiantes.perfilestudiante')),
            ],
            options={'verbose_name': 'archivo de CV', 'verbose_name_plural': 'archivos de CV'},
        ),
        migrations.RunPython(copiar_cv_existentes, migrations.RunPython.noop),
        migrations.RemoveField(model_name='perfilestudiante', name='cv'),
    ]
