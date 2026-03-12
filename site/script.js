(function () {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = lightbox.querySelector('.lightbox__img');
    const lightboxClose = lightbox.querySelector('.lightbox__close');

    document.querySelectorAll('.screenshot').forEach(function (fig) {
        fig.addEventListener('click', function () {
            lightboxImg.src = fig.dataset.full;
            lightboxImg.alt = fig.querySelector('img').alt;
            lightbox.hidden = false;
        });
    });

    lightboxClose.addEventListener('click', function () {
        lightbox.hidden = true;
        lightboxImg.src = '';
    });

    lightbox.addEventListener('click', function (e) {
        if (e.target === lightbox) {
            lightbox.hidden = true;
            lightboxImg.src = '';
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !lightbox.hidden) {
            lightbox.hidden = true;
            lightboxImg.src = '';
        }
    });
})();
