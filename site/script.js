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

/* === Stats Count-Up Animation === */
(function () {
    var statsSection = document.getElementById('stats');
    var statNumbers = statsSection.querySelectorAll('.stats__number');
    var targets = [];

    statNumbers.forEach(function (el) {
        var raw = el.textContent.trim();
        var num = parseInt(raw, 10);
        if (!isNaN(num)) {
            targets.push({ el: el, value: num, isNumber: true });
            el.textContent = '0';
        } else {
            targets.push({ el: el, value: raw, isNumber: false });
            el.classList.add('stats__number--animated');
        }
    });

    function easeOutQuart(t) {
        return 1 - Math.pow(1 - t, 4);
    }

    function animateCountUp(item, delay) {
        setTimeout(function () {
            if (!item.isNumber) {
                item.el.classList.add('is-visible');
                return;
            }
            var duration = 1500;
            var start = null;
            function step(timestamp) {
                if (!start) start = timestamp;
                var elapsed = timestamp - start;
                var progress = Math.min(elapsed / duration, 1);
                var easedProgress = easeOutQuart(progress);
                item.el.textContent = Math.round(easedProgress * item.value);
                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    item.el.textContent = item.value;
                }
            }
            requestAnimationFrame(step);
        }, delay);
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                targets.forEach(function (item, index) {
                    animateCountUp(item, index * 120);
                });
                observer.disconnect();
            }
        });
    }, { threshold: 0.3 });

    observer.observe(statsSection);
})();
