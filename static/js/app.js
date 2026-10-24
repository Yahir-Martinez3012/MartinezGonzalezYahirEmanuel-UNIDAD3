document.addEventListener('DOMContentLoaded', function () {
    // Confirmación antes de acciones delicadas (p. ej. cerrar una vacante)
    document.querySelectorAll('form[data-confirm]').forEach(function (f) {
        f.addEventListener('submit', function (e) {
            if (!confirm(f.dataset.confirm)) { e.preventDefault(); }
        });
    });

    // Validación del CV en el navegador (el servidor vuelve a validar siempre)
    document.querySelectorAll('input[type=file][accept="application/pdf"]').forEach(function (input) {
        input.addEventListener('change', function () {
            var archivo = input.files[0];
            if (!archivo) { return; }
            if (!archivo.name.toLowerCase().endsWith('.pdf')) {
                alert('Selecciona un archivo PDF.'); input.value = '';
            } else if (archivo.size > 5 * 1024 * 1024) {
                alert('El archivo supera los 5 MB.'); input.value = '';
            }
        });
    });

    // Las alertas de éxito se cierran solas
    setTimeout(function () {
        document.querySelectorAll('.alert-success').forEach(function (el) {
            bootstrap.Alert.getOrCreateInstance(el).close();
        });
    }, 6000);
});
