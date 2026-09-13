document.addEventListener('DOMContentLoaded', () => {
  const chips = document.querySelectorAll('.chip');
  const queryBox = document.getElementById('query');

  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      queryBox.value = chip.dataset.query;
      queryBox.focus();
    });
  });
});
