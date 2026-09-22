const menuBtn = document.getElementById("menuBtn");
const navLinks = document.getElementById("navLinks");

menuBtn.addEventListener("click", () => {
    navLinks.classList.toggle("active");
});

const links = document.querySelectorAll(".nav-links a");

links.forEach(link => {
    link.addEventListener("click", () => {
        navLinks.classList.remove("active");
    });
});

const contactBtn = document.getElementById("contactBtn");

contactBtn.addEventListener("click", () => {
    alert("Thanks for reaching out! We'll get back to you soon.");
});