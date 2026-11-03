
(function(){var f=document.querySelector('.where-filter'),tb=document.getElementById('where-table');if(!f||!tb||!window.fetch)return;
var sb=document.getElementById('where-sub'),mn=document.getElementById('where-min'),q=document.getElementById('where-q'),n=document.getElementById('where-n'),
all=document.getElementById('where-all'),segs=[].slice.call(f.querySelectorAll('.seg-b')),rows=null,FIRST=8;
function type(){var on=segs.filter(function(x){return x.getAttribute('aria-pressed')==='true';})[0];return on?on.getAttribute('data-type'):'';}
function draw(){var s=q.value.trim().toLowerCase(),u=sb.value,k=parseInt(mn.value,10),t=type(),hit=rows.filter(function(r){
return(!s||r.n.indexOf(s)>=0)&&(!u||r.u.indexOf(u)>=0)&&r.s>=k&&(!t||r.t===t);});
tb.tBodies[0].innerHTML=hit.slice(0,FIRST).map(function(r){return r.h;}).join('');
[].forEach.call(tb.tBodies[0].rows,function(r){r.style.opacity=1;});
n.textContent=hit.length?'Showing '+Math.min(FIRST,hit.length)+' of '+hit.length+' that match · online clinics first, then by checks':'No seller matches. Try fewer filters.';
var h=[];if(u)h.push('substance='+u);if(k)h.push('min='+k);if(t)h.push('type='+t);if(s)h.push('q='+encodeURIComponent(s));
all.href='/sellers/'+(h.length?'#'+h.join('&'):'');}
function ch(){if(rows)return draw();fetch('/sellers/home.json').then(function(r){return r.json();}).then(function(d){rows=d;draw();});}
f.hidden=false;[sb,mn].forEach(function(x){x.addEventListener('change',ch);});q.addEventListener('input',ch);
segs.forEach(function(x){x.addEventListener('click',function(){segs.forEach(function(y){y.setAttribute('aria-pressed',y===x?'true':'false');});ch();});});})();


(function(){var f=document.querySelector('.legal-check');if(!f)return;
f.addEventListener('submit',function(e){var S=window.pcSearch;if(!S)return;e.preventDefault();var v=document.getElementById('legal-q').value.trim();
S.load(function(d){var r=S.find(d,v,20).filter(function(x){return x.type==='Peptide';});location.href=r.length?r[0].url:'/peptides/';});});})();


(function(){var root=document.getElementById('goals');if(!root)return;
var chips=[].slice.call(root.querySelectorAll('.goal-item')),cur=chips[0].getAttribute('data-goal');
var swapS=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-swap'))/1000||0.2;
root.addEventListener('animationend',function(e){if(e.target.classList.contains('stamp'))root.classList.add('landed');});
function show(k){var p=root.querySelector('.step-panel[data-goal="'+k+'"][data-src]');
if(p){var src=p.getAttribute('data-src');p.removeAttribute('data-src');fetch(src).then(function(r){return r.json();}).then(function(j){p.innerHTML=j.html;if(cur===k)show(k);})
.catch(function(){location.href='/'+k+'/';});return;}
root.querySelectorAll('.step-panel').forEach(function(x){x.hidden=x.getAttribute('data-goal')!==k;if(!x.hidden)root.querySelector('.goal-t').textContent=': '+x.getAttribute('data-title');});
if(!window.pcMotion)return;var on=root.querySelectorAll('.step-panel[data-goal="'+k+'"]');
gsap.fromTo(on,{opacity:0},{opacity:1,duration:swapS,ease:'power1.out'});
gsap.fromTo(root.querySelectorAll('.step-panel[data-goal="'+k+'"] .opt'),{opacity:0,y:4},{opacity:1,y:0,duration:swapS,ease:'power1.out',stagger:0.04});}
function pick(k){if(k===cur)return;cur=k;
root.querySelectorAll('.goal-item,.pin,.region').forEach(function(x){var on=x.getAttribute('data-goal')===k;
if(x.hasAttribute('aria-pressed'))x.setAttribute('aria-pressed',on?'true':'false');x.classList.toggle('on',on);});
var old=root.querySelectorAll('.step-panel:not([hidden])');
if(window.pcMotion&&old.length){gsap.killTweensOf(old);gsap.to(old,{opacity:0,duration:swapS/2,ease:'power1.in',onComplete:function(){gsap.set(old,{opacity:1});if(cur===k)show(k);}});}else{show(k);}}
function hover(k){root.querySelectorAll('.region,.pin').forEach(function(x){x.classList.toggle('hov',x.getAttribute('data-goal')===k);});}
root.addEventListener('click',function(e){var b=e.target.closest('.goal-item,.pin');if(b)pick(b.getAttribute('data-goal'));});
root.addEventListener('mouseover',function(e){var b=e.target.closest('.goal-item,.pin');hover(b?b.getAttribute('data-goal'):null);});
root.addEventListener('mouseleave',function(){hover(null);});
root.addEventListener('keydown',function(e){var t=e.target;
if(t.classList&&t.classList.contains('pin')&&(e.key==='Enter'||e.key===' ')){e.preventDefault();pick(t.getAttribute('data-goal'));return;}
// Arrow keys move to the next or previous chip and choose it (Tab, Enter and Space work as on any button).
var i=chips.indexOf(t);if(i<0)return;var d={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[e.key];if(!d)return;
e.preventDefault();var n=chips[(i+d+chips.length)%chips.length];n.focus();pick(n.getAttribute('data-goal'));});
// /#goals-<slug> (the header's goal menu) chooses that goal on load and when the hash changes.
function fromHash(){var m=location.hash.match(/^#goals-([a-z0-9-]+)$/);
if(m&&root.querySelector('.goal-item[data-goal="'+m[1]+'"]')){pick(m[1]);root.scrollIntoView();}}
fromHash();window.addEventListener('hashchange',fromHash);})();


(function(){if(!window.HTMLDialogElement)return;document.documentElement.classList.add('sellers-js');
document.addEventListener('click',function(e){var b=e.target.closest('.sellers-open');if(b){var d=document.getElementById(b.getAttribute('data-dlg'));
if(d){e.preventDefault();d.showModal();return;}var src=b.getAttribute('data-src');if(!src)return;e.preventDefault();
fetch(src).then(function(r){return r.json();}).then(function(j){document.querySelector('.sellers-all').insertAdjacentHTML('beforeend',j.html);
var n=document.getElementById(b.getAttribute('data-dlg'));n.querySelectorAll('tbody > tr').forEach(function(t){t.style.opacity='1';});
n.showModal();}).catch(function(){location.href=b.href;});return;}
var d=e.target.closest('.sellers-dlg');if(d&&e.target===d)d.close();});})();
