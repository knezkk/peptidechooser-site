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
(function(){var K='pc_state',S={AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'District of Columbia',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'},cur='';
try{cur=localStorage.getItem(K)||'';}catch(x){}if(!S[cur])cur='';
function one(s){if(s.options.length<2)Object.keys(S).sort(function(a,b){return S[a].localeCompare(S[b]);}).forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k+' '+S[k];s.appendChild(o);});
s.value=cur||'all';s.closest('.state-filter').hidden=false;var id=s.getAttribute('data-state-for'),r=id?document.getElementById(id):s.closest('[data-state-root]');if(!r)return;
var all={},ok={};[].forEach.call(r.querySelectorAll('tr[data-clinic]'),function(t){var c=t.getAttribute('data-clinic'),out=cur&&(' '+(t.getAttribute('data-no')||'')+' ').indexOf(' '+cur+' ')>=0;
all[c]=1;if(out)t.setAttribute('data-state-out','');else{t.removeAttribute('data-state-out');ok[c]=1;}});
var n=r.querySelector('.state-n');if(n){var w=s.getAttribute('data-noun'),m=Object.keys(all).length,x=m-Object.keys(ok).length;n.hidden=!cur;
n.textContent=!cur?'':x?x+' of '+m+' '+(x===1?w.slice(0,-1)+' does':w+' do')+' not ship to '+S[cur]:'No '+w.slice(0,-1)+' here is known to skip '+S[cur];}}
function paint(){[].forEach.call(document.querySelectorAll('select[data-state]'),one);}
window.pcState=paint;
document.addEventListener('change',function(e){var s=e.target;if(!s.matches||!s.matches('select[data-state]'))return;cur=s.value==='all'?'':s.value;try{if(cur)localStorage.setItem(K,cur);else localStorage.removeItem(K);}catch(x){}paint();document.dispatchEvent(new Event('pc-state'));});
paint();if(cur)document.dispatchEvent(new Event('pc-state'));})();

(function(){var path=location.pathname,pt=document.body&&document.body.getAttribute('data-pt')||'other',bits=path.split('/'),base={page_type:pt,page_path:path};
if(pt==='seller')base.seller=bits[2];if(pt==='peptide')base.substance=bits[2];if(pt==='goal')base.goal=bits[1];
function send(n,o){try{if(!window.pcGA)return;var p={},k;for(k in base)p[k]=base[k];for(k in o)if(o[k]||o[k]===0)p[k]=o[k];gtag('event',n,p);}catch(x){}}
window.pcEv=send;
function own(el){var o={},g=el.closest('[data-goal]');[].forEach.call(el.attributes,function(a){if(a.name.indexOf('data-ev-')===0)o[a.name.slice(8)]=/^\d+(\.\d+)?$/.test(a.value)?Number(a.value):a.value;});
if(g&&!o.goal)o.goal=g.getAttribute('data-goal');return o;}
function typed(s){var i=document.querySelector(s);return i?i.value.trim().length:0;}
function letter(a){var m=/\/warning-letters\/([^\/]+)/.exec(a.pathname);return m&&m[1].indexOf('about-')!==0?m[1].slice(0,100):'none';}
document.addEventListener('click',function(e){try{var t=e.target;if(!t||!t.closest)return;
var a=t.closest('a[href]'),el=t.closest('[data-ev]'),c=t.closest('[data-card]'),f=t.closest('button[data-filter]'),r=t.closest('#hs-list a,#sp-results a');
if(a&&/(^|\.)fda\.gov$/.test(a.hostname))send('outbound_fda',{letter:letter(a)});
if(c&&t.closest('a,button')&&!t.closest('.ref'))send('decision_card_click',{card:c.getAttribute('data-card')});
if(r){var k=r.querySelector('.chip');send('search',{query_length:typed(r.closest('#hs-list')?'#hs-q':'#sp-q'),result_type:k?k.textContent.toLowerCase():'other'});}
if(f&&!(f.classList.contains('seg-b')&&f.getAttribute('aria-pressed')==='true'))send('filter_change',{filter:f.getAttribute('data-filter'),value:f.getAttribute('data-value')});
if(el&&el.tagName!=='FORM'&&el.getAttribute('aria-pressed')!=='true')send(el.getAttribute('data-ev'),own(el));
}catch(x){}},true);
document.addEventListener('change',function(e){try{var i=e.target;if(i&&i.getAttribute&&i.getAttribute('data-filter')&&i.tagName!=='BUTTON')send('filter_change',{filter:i.getAttribute('data-filter'),value:i.getAttribute('data-value')||i.value});}catch(x){}},true);
document.addEventListener('submit',function(e){try{var f=e.target;if(f.matches('.head-search,#sp-form')){var n=f.querySelector('input').value.trim().length;if(n)send('search',{query_length:n,result_type:'page'});}
else if(f.getAttribute('data-ev')==='newsletter_submit')send('newsletter_submit',{});}catch(x){}},true);})();
