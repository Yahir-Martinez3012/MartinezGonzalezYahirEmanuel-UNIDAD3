from django.core.exceptions import ValidationError

MAX_CV_MB = 5


def validar_cv_pdf(archivo):
    """Valida extensión, tamaño y contenido real del archivo.

    La especificación de PDF permite que la firma ``%PDF-`` aparezca en los primeros
    1024 bytes (algunos generadores anteponen espacios o metadatos), por eso no se
    exige que sea exactamente el inicio del archivo.
    """
    if not archivo.name.lower().endswith('.pdf'):
        raise ValidationError('El CV debe ser un archivo con extensión .pdf.')
    if archivo.size > MAX_CV_MB * 1024 * 1024:
        raise ValidationError(f'El CV no puede pesar más de {MAX_CV_MB} MB.')
    cabecera = archivo.read(1024)
    archivo.seek(0)
    if b'%PDF-' not in cabecera:
        raise ValidationError('El archivo no es un PDF válido.')
