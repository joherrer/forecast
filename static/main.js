/* Javascript file */

document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    const header = document.querySelector('.app-header');
    const spotFilter = document.querySelector('[data-spot-filter]');
    const spotResults = document.querySelector('[data-spot-results]');
    const emptyState = document.querySelector('[data-empty-spots]');

    alerts.forEach((alertElement) => {
        window.setTimeout(() => {
            if (alertElement.classList.contains('show')) {
                const alertInstance = bootstrap.Alert.getOrCreateInstance(alertElement);
                alertInstance.close();
            }
        }, 5000);
    });

    if (header) {
        const syncHeaderState = () => {
            header.classList.toggle('app-header-scrolled', window.scrollY > 12);
        };

        syncHeaderState();
        window.addEventListener('scroll', syncHeaderState, { passive: true });
    }

    if (spotFilter && spotResults && emptyState) {
        const spotCards = Array.from(spotResults.querySelectorAll('[data-spot-name]'));

        const applyFilter = () => {
            const query = spotFilter.value.trim().toLowerCase();
            let visibleCount = 0;

            spotCards.forEach((card) => {
                const matches = card.dataset.spotName.includes(query);
                card.classList.toggle('d-none', !matches);
                if (matches) {
                    visibleCount += 1;
                }
            });

            emptyState.classList.toggle('d-none', visibleCount > 0);
        };

        spotFilter.addEventListener('input', applyFilter);
    }
});
