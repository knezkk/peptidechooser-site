// Header categories (pages.md, Every page, Header; owner task 3 Nov 2026): one open at a time. From 1180px a mouse opens
// a category on hover and closes it 250ms after leaving; a click, Enter or Space opens it too (a mouse click never closes
// one the hover opened). Arrow keys: left and right between the categories, down into the panel, up and down inside it.
// Escape, a click outside or focus leaving closes it. Under 1180px the same buttons open the accordion inside the Menu.
(function(){var cats=[].slice.call(document.querySelectorAll('.nav-cat'));if(!cats.length)return;
var btns=cats.map(function(c){return c.querySelector('.nav-cat-btn');}),wide=matchMedia('(min-width: 1180px)'),t=null,ptr='';
function cur(){for(var j=0;j<cats.length;j++)if(cats[j].classList.contains('open'))return j;return -1;}
function set(i){clearTimeout(t);cats.forEach(function(c,j){c.classList.toggle('open',j===i);btns[j].setAttribute('aria-expanded',j===i?'true':'false');});if(i>=0)place(i);}
// the card under its item (owner task 3 Nov 2026): left edge on the item's, moved left so it ends 24px inside the container
function place(i){var pn=cats[i].querySelector('.nav-panel'),h=document.querySelector('.site-head'),w=h&&h.querySelector('.wrap');if(!w)return;
if(!wide.matches){pn.style.left='';return;}var r=w.getBoundingClientRect(),cs=getComputedStyle(w),L=r.left+parseFloat(cs.paddingLeft),R=r.right-parseFloat(cs.paddingRight);
var x=Math.max(L,Math.min(btns[i].getBoundingClientRect().left,R-24-pn.offsetWidth));pn.style.left=Math.round(x-h.getBoundingClientRect().left)+'px';}
window.addEventListener('resize',function(){var i=cur();if(i>=0)place(i);});
function links(i){return [].slice.call(cats[i].querySelectorAll('.nav-panel a'));}
cats.forEach(function(c,i){var b=btns[i];
b.addEventListener('pointerdown',function(e){ptr=e.pointerType;});
b.addEventListener('click',function(){var m=ptr==='mouse'&&wide.matches;ptr='';set(m||cur()!==i?i:-1);});
c.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'&&wide.matches)set(i);});
c.addEventListener('pointerleave',function(e){if(e.pointerType==='mouse'&&wide.matches&&cur()===i){clearTimeout(t);t=setTimeout(function(){set(-1);},250);}});
b.addEventListener('keydown',function(e){var k=e.key,n=btns.length;
if(wide.matches&&(k==='ArrowRight'||k==='ArrowLeft')){e.preventDefault();var j=(i+(k==='ArrowRight'?1:n-1))%n;btns[j].focus();if(cur()>=0)set(j);}
else if(k==='ArrowDown'){e.preventDefault();set(i);var l=links(i);if(l[0])l[0].focus();}});
c.querySelector('.nav-panel').addEventListener('keydown',function(e){var l=links(i),p=l.indexOf(document.activeElement);if(p<0)return;
if(e.key==='ArrowDown'){e.preventDefault();l[(p+1)%l.length].focus();}
else if(e.key==='ArrowUp'){e.preventDefault();if(p===0)b.focus();else l[p-1].focus();}});});
document.addEventListener('click',function(e){if(cur()>=0&&!e.target.closest('.nav-cat,.nav-toggle'))set(-1);});
document.addEventListener('focusin',function(e){if(wide.matches&&cur()>=0&&!e.target.closest('.nav-cat'))set(-1);});
// registered before the Menu's own Escape, so the first Escape closes only the open category
document.addEventListener('keydown',function(e){var i=cur();if(e.key==='Escape'&&i>=0&&wide.matches){e.stopImmediatePropagation();set(-1);btns[i].focus();}});
wide.addEventListener('change',function(){set(-1);});
var tg=document.querySelector('.nav-toggle');if(tg)tg.addEventListener('click',function(){if(tg.getAttribute('aria-expanded')!=='true'&&cur()<0)set(0);});})();
(function(){var b=document.querySelector('.nav-toggle'),n=document.getElementById('site-nav');if(!b||!n)return;
function set(o){n.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false');}
// opening the menu moves focus to its first visible link: the links come before the button in the page, so Tab alone
// would skip them (design/site-polish, 2 Nov 2026)
b.addEventListener('click',function(){var o=!n.classList.contains('open');set(o);if(o){var f=[].filter.call(n.querySelectorAll('a,button,input'),function(x){return x.offsetParent;})[0];if(f)f.focus();}});
n.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
// phones (owner task 3 Nov 2026, the 390px walkthrough): "Search" beside "Menu" opens the menu with the search field
// focused, and a tap anywhere outside the open menu closes it
var st=document.querySelector('.search-toggle'),q=document.getElementById('hs-q');
if(st&&q)st.addEventListener('click',function(){if(!n.classList.contains('open'))b.click();q.focus();});
document.addEventListener('click',function(e){if(n.classList.contains('open')&&!e.target.closest('#site-nav,.nav-toggle,.search-toggle,.head-search,.head-cta'))set(false);});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&n.classList.contains('open')){set(false);b.focus();}});})();
