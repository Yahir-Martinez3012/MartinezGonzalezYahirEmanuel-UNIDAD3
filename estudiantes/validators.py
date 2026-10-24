from django.core.exceptions import ValidationError

MAX_CV_MB = 5


def validar_cv_pdf(archivo):
    """Valida extensión, tamaño y firma real del archivo (los PDF empiezan con %PDF-)."""
    if not archivo.name.lower().endswith('.pdf'):
        raise ValidationError('El CV debe ser un archivo con extensión .pdf.')
    if archivo.size > MAX_CV_MB * 1024 * 1024:
        raise ValidationError(f'El CV no puede pesar más de {MAX_CV_MB} MB.')
    cabecera = archivo.read(5)
    archivo.seek(0)
    if cabecera != b'%PDF-':
        raise ValidationError('El archivo no es un PDF válido.')
