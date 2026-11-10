import time

from django.core.management.base import BaseCommand

from vacantes.models import Vacante


class Command(BaseCommand):
    help = 'Obtiene las coordenadas (OpenStreetMap/Nominatim) de las vacantes que aún no las tienen.'

    def add_arguments(self, parser):
        parser.add_argument('--todas', action='store_true', help='Vuelve a consultar también las que ya tienen coordenadas.')

    def handle(self, *args, **opciones):
        vacantes = Vacante.objects.exclude(modalidad=Vacante.Modalidad.REMOTA)
        if not opciones['todas']:
            vacantes = vacantes.filter(latitud__isnull=True)
        total = encontradas = 0
        for vacante in vacantes:
            total += 1
            vacante.actualizar_coordenadas()
            if vacante.tiene_coordenadas:
                encontradas += 1
            self.stdout.write(f'  {"✔" if vacante.tiene_coordenadas else "✘"} {vacante.titulo} → {vacante.ubicacion}')
            time.sleep(1.1)       # Nominatim permite como máximo 1 petición por segundo
        self.stdout.write(self.style.SUCCESS(f'{encontradas} de {total} vacantes geocodificadas.'))
