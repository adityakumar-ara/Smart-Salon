// static/js/pwa-register.js
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/js/serviceworker.js')
      .then((registration) => {
        console.log('PWA ServiceWorker registered successfully!');
      })
      .catch((error) => {
        console.log('ServiceWorker registration failed:', error);
      });
  });
}