/** @odoo-module **/

function initCountdown() {
    const input = document.getElementById("remaining_seconds");
    const timer = document.getElementById("countdown_timer");
    const loginButton = document.querySelector("button[type='submit']");
    // રેડ એલર્ટ બોક્સ મેળવવા માટે
    const alertBox = timer ? timer.closest('.alert-danger') : null;

    if (!input || !timer || timer.classList.contains('timer-active')) {
        return;
    }

    timer.classList.add('timer-active');
    let sec = parseInt(input.value, 10) || 0;

    // જો હજુ ટાઈમ બાકી હોય તો બટન ડીસેબલ કરો
    if (sec > 0 && loginButton) {
        loginButton.disabled = true;
        loginButton.style.opacity = "0.6";
        loginButton.style.cursor = "not-allowed";
    }

    function formatTime(seconds) {
        if (seconds < 60) return `${seconds} second(s)`;
        const minutes = Math.floor(seconds / 60);
        return `${minutes} minute(s) ${seconds % 60} second(s)`;
    }

    function updateCountdown() {
        timer.textContent = formatTime(sec);

        if (sec <= 0) {
            clearInterval(interval);

            // ૧. પેજ રીલોડ કર્યા વગર માત્ર રેડ બોક્સને સ્ક્રીન પરથી હટાવી દો
            if (alertBox) {
                alertBox.remove();
            }

            // ૨. લોગિન બટનને પાછું નોર્મલ અને એક્ટિવ કરી દો
            if (loginButton) {
                loginButton.disabled = false;
                loginButton.style.opacity = "1";
                loginButton.style.cursor = "pointer";
            }
            return;
        }
        sec--;
    }

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
}

const observer = new MutationObserver(() => initCountdown());
if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
} else {
    document.addEventListener("DOMContentLoaded", () => {
        observer.observe(document.body, { childList: true, subtree: true });
    });
}