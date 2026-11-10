
(function(){var idx=null,wait=[],ORDER={Goal:0,Peptide:1,Seller:2,Clinic:3,Comparison:4,Guide:5,Page:6};
function load(cb){if(idx)return cb(idx);wait.push(cb);if(wait.length>1)return;
fetch('/search-index.json').then(function(r){return r.json();}).then(function(d){idx=d;var w=wait;wait=[];w.forEach(function(f){f(d);});}).catch(function(){wait=[];});}
function c(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,'');}
function score(f,k){var cf=c(f);if(cf.indexOf(k)===0)return 3;var ws=String(f).toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
for(var i=1;i<ws.length;i++){if(c(ws.slice(i).join('')).indexOf(k)===0)return 2;}return cf.indexOf(k)>=0?1:0;}
function find(d,q,n){var k=c(q);if(!k)return[];var out=[];
d.forEach(function(e){var s=score(e.name,k)*2;(e.aliases||[]).forEach(function(a){s=Math.max(s,score(a,k)*2-1);});if(s>0)out.push([s,e]);});
out.sort(function(x,y){return y[0]-x[0]||ORDER[x[1].type]-ORDER[y[1].type]||x[1].name.length-y[1].name.length||(x[1].name<y[1].name?-1:1);});
return out.slice(0,n).map(function(x){return x[1];});}
function row(e,tab){var li=document.createElement('li'),a=document.createElement('a');a.href=e.url;if(!tab)a.tabIndex=-1;
[['search-name',e.name],['chip chip-neutral',e.type],['search-line',e.line]].forEach(function(p){var s=document.createElement('span');s.className=p[0];s.textContent=p[1];a.appendChild(s);});
li.appendChild(a);return li;}
window.pcSearch={load:load,find:find,row:row};
var f=document.querySelector('.head-search');if(!f)return;var inp=f.querySelector('input'),list=f.querySelector('.search-list'),res=[],act=-1;
function close(){list.hidden=true;inp.setAttribute('aria-expanded','false');inp.removeAttribute('aria-activedescendant');act=-1;}
function draw(){var v=inp.value.trim();if(!v){close();return;}load(function(d){if(inp.value.trim()!==v)return;res=find(d,v,8);list.textContent='';act=-1;
inp.removeAttribute('aria-activedescendant');
if(!res.length){var li=document.createElement('li');li.className='search-none';li.textContent='No match. Press Enter to search every page.';list.appendChild(li);}
res.forEach(function(e,i){var li=row(e);li.id='hs-o'+i;li.setAttribute('role','option');li.setAttribute('aria-selected','false');list.appendChild(li);});
list.hidden=false;inp.setAttribute('aria-expanded','true');});}
function mark(i){var o=list.querySelectorAll('[role=option]');if(!o.length)return;act=(i+o.length)%o.length;
for(var j=0;j<o.length;j++)o[j].setAttribute('aria-selected',j===act?'true':'false');inp.setAttribute('aria-activedescendant',o[act].id);o[act].scrollIntoView({block:'nearest'});}
inp.addEventListener('input',draw);inp.addEventListener('focus',function(){load(function(){});if(inp.value.trim())draw();});
inp.addEventListener('keydown',function(e){if(e.key==='ArrowDown'){e.preventDefault();if(list.hidden)draw();else mark(act+1);}
else if(e.key==='ArrowUp'){e.preventDefault();if(!list.hidden)mark(act-1);}
else if(e.key==='Enter'&&!list.hidden&&act>=0&&res[act]){e.preventDefault();if(window.pcEv)pcEv('search',{query_length:inp.value.trim().length,result_type:String(res[act].type).toLowerCase()});location.href=res[act].url;}
else if(e.key==='Escape'&&!list.hidden){e.preventDefault();e.stopPropagation();close();}});
document.addEventListener('click',function(e){if(!f.contains(e.target))close();});})();


(function(){var f=document.querySelector('.legal-check');if(!f)return;
f.addEventListener('submit',function(e){var S=window.pcSearch;if(!S)return;e.preventDefault();var v=document.getElementById('legal-q').value.trim();
S.load(function(d){var r=S.find(d,v,20).filter(function(x){return x.type==='Peptide';});if(window.pcEv)pcEv(f.getAttribute('data-ev'),{substance:r.length?r[0].url.split('/')[2]:'none'});location.href=r.length?r[0].url:'/peptides/';});});})();


window.pcFig=function(box,choose){
var stage=box.querySelector('.fig3d-stage'),label=box.querySelector('.fig3d-label'),back=box.querySelector('.fig3d-back');
var base=box.getAttribute('data-base'),views=JSON.parse(box.getAttribute('data-views')),pins=[].slice.call(box.querySelectorAll('.pin'));
var view=box.querySelector('.fig3d-view'),cur=null,layers={},tween=null,token=0;
var zoomS=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--motion-zoom'))/1000||0.7;
// From 900px a pin is a control of its own. Below that seven do not fit: they are markers, and the whole figure and the goal rows are the targets.
var wide=window.matchMedia('(min-width: 900px)');
function roles(){pins.forEach(function(p){if(wide.matches){p.setAttribute('role','button');p.tabIndex=0;p.removeAttribute('aria-hidden');}else{p.removeAttribute('role');p.removeAttribute('tabindex');p.setAttribute('aria-hidden','true');}});}
roles();if(wide.addEventListener)wide.addEventListener('change',roles);
function rect(k){var z=views[k].z,h=1/z;return {z:z,x:(1-h)/2,y:Math.min(1-h,Math.max(0,views[k].v-h/2))};}
function ensure(k){if(layers[k])return layers[k];var r=rect(k),out=[];
function add(name){var i=new Image();i.alt='';i.className='fig3d-layer';i.style.left=r.x*100+'%';i.style.top=r.y*100+'%';i.style.width=100/r.z+'%';i.style.height=100/r.z+'%';i.src=base+name;stage.insertBefore(i,pins[0]);out.push(i);}
if(r.z>1)add(k+'.webp');add(k+'-glow.webp');layers[k]=out;return out;}
function ready(l){return Promise.all(l.map(function(i){return i.decode?i.decode().catch(function(){}):0;}));}
function move(r,animate,done){if(tween){tween.kill();tween=null;}
var to={xPercent:-r.x*r.z*100,yPercent:-r.y*r.z*100,scale:r.z};
if(animate){to.duration=zoomS;to.ease='power2.out';to.onUpdate=function(){stage.style.setProperty('--s',gsap.getProperty(stage,'scaleX'));};
to.onComplete=function(){stage.style.setProperty('--s',r.z);done();};tween=gsap.to(stage,to);return;}
if(window.gsap)gsap.set(stage,to);else stage.style.transform='translate('+to.xPercent+'%,'+to.yPercent+'%) scale('+r.z+')';
stage.style.setProperty('--s',r.z);done();}
function clear(){Object.keys(layers).forEach(function(k){layers[k].forEach(function(i){i.classList.remove('in');});});label.hidden=true;}
function place(k){var p=box.querySelector('.pin[data-goal="'+k+'"]');label.textContent=p.getAttribute('aria-label');label.hidden=false;label.style.left='0';label.style.top='0';
var b=box.getBoundingClientRect(),q=p.getBoundingClientRect(),x=q.left+q.width/2-b.left,y=q.top+q.height/2-b.top,w=label.offsetWidth,h=label.offsetHeight,g=14,lx,ly=y-h/2;
if(x+g+w<=b.width-4)lx=x+g;else if(x-g-w>=4)lx=x-g-w;else{lx=Math.max(4,Math.min(b.width-w-4,x-w/2));ly=y+g;if(ly+h>back.offsetTop-4)ly=y-g-h;}
label.style.left=lx+'px';label.style.top=Math.max(4,Math.min(b.height-h-4,ly))+'px';}
function go(k){if(cur===k)return;var t=++token,list=ensure(k),anim=!!window.pcMotion;cur=k;clear();box.classList.add('zoomed');view.classList.toggle('near',rect(k).z>1);back.hidden=false;
pins.forEach(function(p){var on=p.getAttribute('data-goal')===k;p.classList.toggle('on',on);p.setAttribute('aria-pressed',on?'true':'false');});
var land=function(){ready(list).then(function(){if(t!==token)return;list.forEach(function(i){i.classList.add('in');});place(k);});};
if(anim)move(rect(k),true,land);else ready(list).then(function(){if(t===token)move(rect(k),false,land);});}
function out(refocus){if(!cur)return;var k=cur;token++;cur=null;clear();box.classList.remove('zoomed');view.classList.remove('near');back.hidden=true;
move({z:1,x:0,y:0},!!window.pcMotion,function(){});
if(refocus){var p=box.querySelector('.pin[data-goal="'+k+'"]');if(p)p.focus();}}
box.addEventListener('click',function(e){
if(e.target.closest('.fig3d-back')){out(true);return;}
var p=e.target.closest('.pin');
if(cur){if(!p)out(false);return;}
var best=null,d=Infinity;pins.forEach(function(x){var q=x.getBoundingClientRect(),n=Math.hypot(e.clientX-q.left-q.width/2,e.clientY-q.top-q.height/2);if(n<d){d=n;best=x;}});
if(best&&d<=Math.max(44,box.offsetHeight*0.2))pinPick(best.getAttribute('data-goal'));});
function pinPick(k){if(window.pcEv)pcEv('goal_pick',{goal:k});choose(k);}
function pre(e){var p=e.target.closest&&e.target.closest('.pin');if(p)ensure(p.getAttribute('data-goal'));}
box.addEventListener('mouseover',pre);box.addEventListener('focusin',pre);
box.addEventListener('keydown',function(e){if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('pin')){e.preventDefault();pinPick(e.target.getAttribute('data-goal'));}});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&cur)out(box.contains(document.activeElement));});
return {go:go,out:out,preload:ensure};};


(function(){var root=document.getElementById('goals');if(!root)return;
var chips=[].slice.call(root.querySelectorAll('.goal-item')),cur=chips[0].getAttribute('data-goal');
var figBox=root.querySelector('.fig3d'),fig=figBox&&window.pcFig?pcFig(figBox,act):null;
function act(k){pick(k);if(fig)fig.go(k);}
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
root.querySelectorAll('.goal-item,.pin').forEach(function(x){var on=x.getAttribute('data-goal')===k;
if(x.hasAttribute('aria-pressed'))x.setAttribute('aria-pressed',on?'true':'false');x.classList.toggle('on',on);});
var old=root.querySelectorAll('.step-panel:not([hidden])');
if(window.pcMotion&&old.length){gsap.killTweensOf(old);gsap.to(old,{opacity:0,duration:swapS/2,ease:'power1.in',onComplete:function(){gsap.set(old,{opacity:1});if(cur===k)show(k);}});}else{show(k);}}
function hover(k){root.querySelectorAll('.pin').forEach(function(x){x.classList.toggle('hov',x.getAttribute('data-goal')===k);});if(k&&fig)fig.preload(k);}
root.addEventListener('click',function(e){var b=e.target.closest('.goal-item');if(b)act(b.getAttribute('data-goal'));});
root.addEventListener('mouseover',function(e){var b=e.target.closest('.goal-item,.pin');hover(b?b.getAttribute('data-goal'):null);});
root.addEventListener('mouseleave',function(){hover(null);});
root.addEventListener('keydown',function(e){var t=e.target;
// Arrow keys move to the next or previous chip and choose it (Tab, Enter and Space work as on any button).
var i=chips.indexOf(t);if(i<0)return;var d={ArrowRight:1,ArrowDown:1,ArrowLeft:-1,ArrowUp:-1}[e.key];if(!d)return;
e.preventDefault();var n=chips[(i+d+chips.length)%chips.length];n.focus();if(window.pcEv)pcEv('goal_pick',{goal:n.getAttribute('data-goal')});act(n.getAttribute('data-goal'));});
// /#goals-<slug> (the header's goal menu) chooses that goal on load and when the hash changes.
function fromHash(){var m=location.hash.match(/^#goals-([a-z0-9-]+)$/);
if(m&&root.querySelector('.goal-item[data-goal="'+m[1]+'"]')){act(m[1]);root.scrollIntoView();}}
fromHash();window.addEventListener('hashchange',fromHash);})();


(function(){if(!window.HTMLDialogElement)return;document.documentElement.classList.add('sellers-js');
document.addEventListener('click',function(e){var b=e.target.closest('.sellers-open');if(b){var d=document.getElementById(b.getAttribute('data-dlg'));
if(d){e.preventDefault();d.showModal();return;}var src=b.getAttribute('data-src');if(!src)return;e.preventDefault();
fetch(src).then(function(r){return r.json();}).then(function(j){document.querySelector('.sellers-all').insertAdjacentHTML('beforeend',j.html);
var n=document.getElementById(b.getAttribute('data-dlg'));n.querySelectorAll('tbody > tr').forEach(function(t){t.style.opacity='1';});
if(window.pcState)pcState();n.showModal();}).catch(function(){location.href=b.href;});return;}
var d=e.target.closest('.sellers-dlg');if(d&&e.target===d)d.close();});})();
