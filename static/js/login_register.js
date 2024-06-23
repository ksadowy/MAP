const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});

document.getElementById('login').addEventListener('click', () => {
    container.classList.remove("right-panel-active");
});

document.getElementById('register').addEventListener('click', () => {
    container.classList.add("right-panel-active");
});