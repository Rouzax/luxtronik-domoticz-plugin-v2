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

/* === Device Card Sparkline Charts === */
(function () {
    /* Sample sparkline data per card name (24h of data points) */
    var sparklines = {
        'COP total': { color: '#06b6d4', d: 'M0,35 L12,32 L25,28 L37,30 L50,25 L62,20 L75,18 L87,22 L100,20 L112,15 L125,12 L137,10 L150,8 L162,12 L175,15 L187,18 L200,22 L212,25 L225,28 L237,30 L250,32 L262,28 L275,25 L287,22 L300,20' },
        'COP heating': { color: '#22c55e', d: 'M0,30 L12,28 L25,22 L37,18 L50,15 L62,12 L75,10 L87,8 L100,10 L112,12 L125,8 L137,6 L150,5 L162,8 L175,10 L187,15 L200,18 L212,20 L225,22 L237,18 L250,15 L262,12 L275,10 L287,8 L300,10' },
        'COP DHW': { color: '#f59e0b', d: 'M0,40 L12,42 L25,45 L37,20 L50,15 L62,25 L75,35 L87,38 L100,40 L112,42 L125,44 L137,22 L150,18 L162,28 L175,36 L187,40 L200,42 L212,44 L225,46 L237,24 L250,18 L262,30 L275,38 L287,42 L300,44' },
        'Power total': { color: '#f59e0b', d: 'M0,50 L12,50 L25,48 L37,10 L50,8 L62,10 L75,12 L87,50 L100,50 L112,50 L125,48 L137,8 L150,10 L162,12 L175,50 L187,50 L200,50 L212,48 L225,10 L237,8 L250,10 L262,50 L275,50 L287,50 L300,50' },
        'Heat out total': { color: '#ef4444', d: 'M0,50 L12,50 L25,45 L37,12 L50,10 L62,15 L75,20 L87,50 L100,50 L112,48 L125,42 L137,10 L150,12 L162,18 L175,50 L187,50 L200,50 L212,45 L225,12 L237,10 L250,15 L262,50 L275,50 L287,50 L300,50' },
        'Outside temp': { color: '#38bdf8', d: 'M0,48 L12,46 L25,42 L37,38 L50,32 L62,25 L75,20 L87,15 L100,12 L112,10 L125,12 L137,15 L150,20 L162,25 L175,28 L187,30 L200,28 L212,25 L225,22 L237,20 L250,22 L262,25 L275,28 L287,32 L300,35' },
        'Room temp': { color: '#f97316', d: 'M0,22 L12,22 L25,23 L37,24 L50,24 L62,23 L75,22 L87,20 L100,18 L112,16 L125,15 L137,16 L150,18 L162,20 L175,22 L187,22 L200,22 L212,22 L225,23 L237,23 L250,22 L262,22 L275,22 L287,22 L300,22' },
        'DHW temp': { color: '#ef4444', d: 'M0,28 L12,30 L25,35 L37,40 L50,42 L62,45 L75,22 L87,10 L100,8 L112,10 L125,15 L137,20 L150,28 L162,32 L175,38 L187,42 L200,45 L212,20 L225,10 L237,8 L250,12 L262,18 L275,25 L287,30 L300,35' },
        'Heat supply temp': { color: '#f97316', d: 'M0,30 L12,30 L25,28 L37,15 L50,10 L62,12 L75,15 L87,30 L100,30 L112,28 L125,25 L137,12 L150,10 L162,14 L175,30 L187,30 L200,30 L212,28 L225,14 L237,10 L250,12 L262,30 L275,30 L287,30 L300,30' },
        'Heat return temp': { color: '#f97316', d: 'M0,25 L12,25 L25,24 L37,18 L50,15 L62,16 L75,20 L87,25 L100,25 L112,24 L125,22 L137,16 L150,14 L162,18 L175,25 L187,25 L200,25 L212,24 L225,18 L237,14 L250,16 L262,25 L275,25 L287,25 L300,25' },
        'Source inlet temp': { color: '#22c55e', d: 'M0,20 L12,20 L25,22 L37,22 L50,22 L62,22 L75,20 L87,18 L100,18 L112,20 L125,20 L137,22 L150,22 L162,22 L175,20 L187,18 L200,18 L212,20 L225,20 L237,22 L250,22 L262,22 L275,20 L287,18 L300,18' },
        'Compressor freq': { color: '#06b6d4', d: 'M0,50 L12,50 L25,50 L37,15 L50,12 L62,15 L75,18 L87,50 L100,50 L112,50 L125,50 L137,10 L150,12 L162,15 L175,50 L187,50 L200,50 L212,50 L225,12 L237,10 L250,15 L262,50 L275,50 L287,50 L300,50' },
        'Compressor capacity': { color: '#06b6d4', d: 'M0,50 L12,50 L25,48 L37,25 L50,22 L62,25 L75,28 L87,50 L100,50 L112,48 L125,45 L137,20 L150,22 L162,25 L175,50 L187,50 L200,50 L212,48 L225,22 L237,20 L250,25 L262,50 L275,50 L287,50 L300,50' },
        'Superheat': { color: '#22c55e', d: 'M0,25 L12,24 L25,22 L37,18 L50,20 L62,22 L75,24 L87,25 L100,24 L112,22 L125,20 L137,18 L150,20 L162,22 L175,25 L187,24 L200,22 L212,20 L225,18 L237,20 L250,22 L262,24 L275,25 L287,24 L300,22' },
        'Pressure high': { color: '#f59e0b', d: 'M0,40 L12,40 L25,38 L37,18 L50,15 L62,18 L75,20 L87,40 L100,40 L112,38 L125,35 L137,15 L150,18 L162,20 L175,40 L187,40 L200,40 L212,38 L225,18 L237,15 L250,18 L262,40 L275,40 L287,40 L300,40' }
    };

    var activeChart = null;

    document.querySelectorAll('.device-card').forEach(function (card) {
        card.style.cursor = 'pointer';
        card.addEventListener('click', function () {
            var name = card.querySelector('.device-card__name').textContent.trim();
            var data = sparklines[name];

            /* Close if clicking same card */
            if (activeChart && activeChart.parentElement === card) {
                activeChart.remove();
                activeChart = null;
                return;
            }

            /* Close previous */
            if (activeChart) {
                activeChart.remove();
                activeChart = null;
            }

            if (!data) return;

            var chartEl = document.createElement('div');
            chartEl.className = 'device-card__chart';
            chartEl.innerHTML =
                '<span class="device-card__chart-label">24h &middot; ' + name + '</span>' +
                '<svg viewBox="0 0 300 55" preserveAspectRatio="none">' +
                '<defs><linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">' +
                '<stop offset="0%" stop-color="' + data.color + '" stop-opacity="0.3"/>' +
                '<stop offset="100%" stop-color="' + data.color + '" stop-opacity="0"/>' +
                '</linearGradient></defs>' +
                '<path d="' + data.d + ' L300,55 L0,55 Z" fill="url(#cg)"/>' +
                '<path d="' + data.d + '" fill="none" stroke="' + data.color + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
                '</svg>';

            card.appendChild(chartEl);
            activeChart = chartEl;
        });
    });

    /* Close chart on outside click */
    document.addEventListener('click', function (e) {
        if (activeChart && !e.target.closest('.device-card')) {
            activeChart.remove();
            activeChart = null;
        }
    });
})();
