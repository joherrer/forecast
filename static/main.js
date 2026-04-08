/* Javascript file */

document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert.alert-dismissible');

    alerts.forEach((alertElement) => {
        window.setTimeout(() => {
            if (alertElement.classList.contains('show')) {
                const alertInstance = bootstrap.Alert.getOrCreateInstance(alertElement);
                alertInstance.close();
            }
        }, 5000);
    });
});
