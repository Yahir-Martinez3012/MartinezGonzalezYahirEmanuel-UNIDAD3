from django.test import TestCase
from django.urls import reverse


class EncabezadosDeSeguridadTests(TestCase):
    def test_politica_csp_en_las_paginas_publicas(self):
        for nombre in ('inicio', 'vacantes:lista', 'cuentas:login', 'cuentas:registro'):
            r = self.client.get(reverse(nombre))
            csp = r['Content-Security-Policy']
            self.assertIn("default-src 'self'", csp, nombre)
            self.assertIn("object-src 'none'", csp, nombre)
            self.assertIn("frame-ancestors 'none'", csp, nombre)

    def test_solo_se_permiten_scripts_propios_y_del_cdn(self):
        csp = self.client.get(reverse('inicio'))['Content-Security-Policy']
        script = [d for d in csp.split(';') if d.strip().startswith('script-src')][0]
        self.assertIn('https://cdn.jsdelivr.net', script)
        self.assertNotIn('unsafe-inline', script)
        self.assertNotIn('unsafe-eval', script)

    def test_otros_encabezados(self):
        r = self.client.get(reverse('inicio'))
        self.assertEqual(r['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(r['Referrer-Policy'], 'strict-origin-when-cross-origin')
        self.assertEqual(r['X-Frame-Options'], 'DENY')

    def test_las_plantillas_no_tienen_scripts_en_linea(self):
        """Con CSP estricto, un <script> en línea no se ejecutaría: todo el JavaScript va en archivos estáticos."""
        import re
        html = self.client.get(reverse('inicio')).content.decode()
        for apertura in re.findall(r'<script\b[^>]*>', html):
            self.assertIn('src=', apertura)
        self.assertNotRegex(html, r'\son(click|load|submit)\s*=')
