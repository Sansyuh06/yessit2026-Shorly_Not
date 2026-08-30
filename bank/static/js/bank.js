// Bank Portal JavaScript Helpers
document.addEventListener('DOMContentLoaded', () => {
  // Amount Chips Selection
  const chips = document.querySelectorAll('.chip');
  const amountInput = document.getElementById('amount');

  if (chips.length > 0 && amountInput) {
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        amountInput.value = chip.getAttribute('data-val');
      });
    });
  }

  // Quick User Switcher in Login
  const userButtons = document.querySelectorAll('.demo-user-btn');
  const userInput = document.getElementById('username');
  const passInput = document.getElementById('password');

  if (userButtons.length > 0 && userInput && passInput) {
    userButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const u = btn.getAttribute('data-u');
        const p = btn.getAttribute('data-p');
        userInput.value = u;
        passInput.value = p;
      });
    });
  }
});
