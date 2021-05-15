const nav_element = document.getElementById("timetable");

nav_element.addEventListener('mouseenter', showMenu);
nav_element.addEventListener('mouseleave', hideMenu);

function showMenu(){
    this.querySelector(".nav__sub-menu").style.overflow = 'visible';
    this.querySelector(".nav__sub-menu").style.opacity = '1';
    this.querySelector(".nav__sub-menu").style.height = 'auto';
    this.querySelector(".nav__sub-menu").style.border = '1px solid rgba(175, 175, 175, 0.9)';
    this.querySelector(".nav__sub-menu").style.outline = '2px solid rgba(248, 248, 248, 0.8)';
}

function hideMenu(){
    this.querySelector(".nav__sub-menu").style.overflow = 'hidden';
    this.querySelector(".nav__sub-menu").style.opacity = '0';
    this.querySelector(".nav__sub-menu").style.height = '0';
    this.querySelector(".nav__sub-menu").style.border = '0';
    this.querySelector(".nav__sub-menu").style.outline = '0';
    }
