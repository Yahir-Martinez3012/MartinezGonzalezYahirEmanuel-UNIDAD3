// Mapa de la vacante: Leaflet + teselas de OpenStreetMap (servicio de terceros)
document.addEventListener('DOMContentLoaded', function () {
    var contenedor = document.getElementById('mapa');
    if (!contenedor || typeof L === 'undefined') { return; }

    var lat = parseFloat(contenedor.dataset.lat);
    var lng = parseFloat(contenedor.dataset.lng);
    if (isNaN(lat) || isNaN(lng)) { return; }

    var mapa = L.map(contenedor).setView([lat, lng], 13);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(mapa);
    L.marker([lat, lng]).addTo(mapa).bindPopup(contenedor.dataset.titulo);   // Leaflet escapa el texto al crear el popup
});
