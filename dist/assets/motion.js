document.addEventListener('DOMContentLoaded',function(){
var d=document.documentElement;if(!d.classList.contains('motion')||!window.gsap||!window.ScrollTrigger)return;
window.pcMotion=true;gsap.registerPlugin(ScrollTrigger);
var css=getComputedStyle(d),ms=function(n){return parseFloat(css.getPropertyValue('--motion-'+n))/1000;};
var rise=parseFloat(css.getPropertyValue('--motion-rise'));
// table rows rise only in tables of up to 25 rows; a long data table (letters, sellers, legal) shows at once, since one
// trigger per row cost seconds of layout on phones (design/site-polish, 2 Nov 2026). Without :has the rows are not pre-hidden.
var sel='.sec-hd, .criteria li, .creators li';try{if(document.querySelector('.tbl tbody:not(:has(> tr:nth-child(26))) > tr'))sel+=', .tbl tbody:not(:has(> tr:nth-child(26))) > tr';}catch(e){}
// a jump to an anchor (/weight-loss/#clinics) never lands on a hidden heading (owner UX audit B24, 3 Nov 2026): with a
// hash, or on a hash change, everything shows at once; otherwise what is already in or above the window shows on load
var show=function(els){gsap.set(els,{opacity:1,y:0});};
if(location.hash){show(sel);return;}
window.addEventListener('hashchange',function(){ScrollTrigger.getAll().forEach(function(t){t.kill();});show(sel);});
show([].filter.call(document.querySelectorAll(sel),function(el){return el.getBoundingClientRect().top<innerHeight;}));
ScrollTrigger.batch(sel,{start:'top 92%',once:true,
onEnter:function(els){els=els.filter(function(el){return getComputedStyle(el).opacity!=='1';});if(els.length)gsap.fromTo(els,{opacity:0,y:rise},{opacity:1,y:0,duration:ms('reveal'),ease:'power2.out',stagger:ms('stagger'),overwrite:true});}});
});
