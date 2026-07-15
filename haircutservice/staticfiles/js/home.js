
const slider = document.querySelector('.custom-slider');

if (slider) {
    slider.addEventListener('wheel', (evt) => {
        evt.preventDefault();
        slider.scrollLeft += evt.deltaY * 1.2;
    }, { passive: false }); 
}