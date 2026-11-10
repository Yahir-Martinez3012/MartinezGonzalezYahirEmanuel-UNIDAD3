"""Observer: las postulaciones avisan por correo al estudiante cuando se crean o cambian de estado.

La vista que modifica la postulación no sabe nada del correo: solo guarda, y los receptores reaccionan.
"""
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from servicios import correo

from .models import Postulacion


@receiver(pre_save, sender=Postulacion)
def recordar_estado_anterior(sender, instance, **kwargs):
    instance._estado_anterior = (
        Postulacion.objects.filter(pk=instance.pk).values_list('estado', flat=True).first() if instance.pk else None)


@receiver(post_save, sender=Postulacion)
def notificar_al_estudiante(sender, instance, created, **kwargs):
    if not created and getattr(instance, '_estado_anterior', None) == instance.estado:
        return                                           # se guardó sin cambiar el estado
    destinatario = instance.estudiante.usuario.email
    if not destinatario:
        return
    html = render_to_string('correos/postulacion.html', {      # la plantilla escapa los datos (evita inyección de HTML)
        'nombre': instance.estudiante.nombre_visible, 'vacante': instance.vacante.titulo,
        'empresa': instance.vacante.empresa.nombre, 'estado': instance.get_estado_display(), 'creada': created})
    asunto = ('Recibimos tu postulación' if created else 'Cambió el estado de tu postulación') + f' · {instance.vacante.titulo}'
    transaction.on_commit(lambda: correo.enviar(destinatario, asunto, html))      # solo si la transacción se confirmó
