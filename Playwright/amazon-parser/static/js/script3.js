function setupCustomSelect(id, callback) {
    const sel = document.getElementById(id);
    const selected = sel.querySelector('.selected');
    const options = sel.querySelectorAll('.options div');

    let closeTimeout;

    sel.addEventListener('click', e => {
        if (!e.target.closest('.options')) {
          sel.classList.toggle('open');
        }
      });

    options.forEach(opt => {
        opt.addEventListener('click', e => {
            selected.textContent = e.target.textContent;
            sel.classList.remove('open');
            callback(e.target.dataset.value);
            render();
        });
    });

    sel.addEventListener('mouseleave', () => {
        closeTimeout = setTimeout(() => {
            sel.classList.remove('open');
        }, 200);
    });

    sel.addEventListener('mouseenter', () => {
        clearTimeout(closeTimeout);
    });
}

setupCustomSelect('sort-price-select', val => sortPriceValue = val);
setupCustomSelect('sort-rating-select', val => sortRatingValue = val);

const list = document.getElementById("list");
const originalCards = Array.from(list.querySelectorAll(".product-card"));
originalCards.forEach((card, i) => card.dataset.idx = i);

const state = {
    price: "none",
    rating: "none",
    minRating: 0
};

const parseNum = (s) => parseFloat(String(s).replace(",", "."));

