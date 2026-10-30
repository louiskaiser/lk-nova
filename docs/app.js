'use strict';
const locale=document.documentElement.lang;
const messages=window.LKNovaLocales[locale]||window.LKNovaLocales.en;
const axes=[
{tag:'wght',min:500,def:900,max:950},
{tag:'wdth',min:85,def:100,max:140},
{tag:'slnt',min:-12,def:0,max:0},
{tag:'CNTR',min:78,def:92,max:105},
{tag:'ROND',min:25,def:50,max:50},
{tag:'APER',min:26,def:36,max:42},
{tag:'RLEG',min:20,def:80,max:95},
{tag:'XBAR',min:57,def:76,max:76},
{tag:'MARK',min:10,def:20,max:40}
].map((axis,i)=>({...axis,label:messages.axis_labels[i]}));
const languagePaths={'en':'index.html','de-DE':'de/index.html','de-CH':'de-CH/index.html','zh-CN':'zh-CN/index.html'};
const siteRoot=new URL(locale==='en'?'./':'../',location.href);
function supportedLanguage(value){if(!value)return null;const lang=value.toLowerCase();if(lang==='de-ch')return 'de-CH';if(lang.startsWith('de'))return 'de-DE';if(lang.startsWith('en'))return 'en';if(['zh','zh-cn','zh-sg','zh-hans','zh-hans-cn','zh-hans-sg'].includes(lang))return 'zh-CN';return null}
function goToLanguage(lang){const next=new URL(languagePaths[lang],siteRoot);next.searchParams.set('lang',lang);next.hash=location.hash;try{localStorage.setItem('lk-nova-language',lang)}catch(e){}location.replace(next.href)}
const explicit=new URLSearchParams(location.search).get('lang');
let preferred=null;try{preferred=localStorage.getItem('lk-nova-language')}catch(e){}
const desired=supportedLanguage(explicit)||(locale!=='en'?locale:supportedLanguage(preferred)||supportedLanguage(navigator.language)||'en');
if(desired!==locale)goToLanguage(desired);
const languagePicker=document.querySelector('.language-picker');
for(const button of document.querySelectorAll('[data-language]')){if(button.dataset.language===locale)button.setAttribute('aria-current','true');button.addEventListener('click',()=>{stop();try{sessionStorage.setItem('lk-nova-specimen',JSON.stringify({axes:state,text:document.querySelector('#sample-input').value,size:document.querySelector('#preview-size').value}))}catch(e){}goToLanguage(button.dataset.language)})}
document.addEventListener('click',event=>{if(!languagePicker.contains(event.target))languagePicker.open=false});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&languagePicker.open){languagePicker.open=false;languagePicker.querySelector('summary').focus()}});
const $=s=>document.querySelector(s),state=Object.fromEntries(axes.map(a=>[a.tag,a.def]));
const defaults={...state};let running=false,frame=0,start=0,phase=0,restore=null;
const motion=matchMedia('(prefers-reduced-motion: reduce)');
for(const a of axes){
 const el=document.createElement('div');el.className='axis';
 const label=document.createElement('label');label.className='axis-label';label.htmlFor='axis-'+a.tag;
 const name=document.createElement('span');name.textContent=a.label+' ';const tag=document.createElement('code');tag.textContent=a.tag;name.append(tag);
 const out=document.createElement('input');Object.assign(out,{id:'value-'+a.tag,type:'number',min:a.min,max:a.max,step:1,value:a.def});out.className='axis-number';out.setAttribute('aria-label',a.label);out.addEventListener('change',()=>{const value=Number(out.value);stop();state[a.tag]=out.value!==''&&Number.isFinite(value)?Math.max(a.min,Math.min(a.max,value)):a.def;clearPresets();render()});out.addEventListener('keydown',event=>{if(event.key==='Enter'){out.blur()}});
 label.append(name,out);
 const input=document.createElement('input');Object.assign(input,{id:'axis-'+a.tag,type:'range',min:a.min,max:a.max,step:1,value:a.def});
 input.addEventListener('input',()=>{const value=Number(input.value);stop();state[a.tag]=value;clearPresets();render()});
 el.append(label,input);$('#axis-controls').append(el);
 const option=document.createElement('option');option.value=a.tag;option.textContent=a.label;$('#animate-axis').append(option);
}
function settings(){return axes.map(a=>'"'+a.tag+'" '+Number(state[a.tag].toFixed(2))).join(', ')}
function render(){
 updatePresetIndicator();
 $('#sample').style.fontVariationSettings=settings();
 for(const a of axes){$('#axis-'+a.tag).value=state[a.tag];$('#value-'+a.tag).value=Math.round(state[a.tag])}
 $('#css-code').textContent='font-family: "LK Nova", sans-serif;\nfont-variation-settings: '+settings()+';\nletter-spacing: -0.05em;\ntext-rendering: geometricPrecision;';
}
function clearPresets(){document.querySelectorAll('[data-preset]').forEach(b=>b.setAttribute('aria-pressed','false'))}
function stop(){if(!running)return;running=false;cancelAnimationFrame(frame);$('#sample').removeAttribute('data-live');if(restore)Object.assign(state,restore);restore=null;$('#play').textContent=messages.start;$('#play').setAttribute('aria-pressed','false');render()}
function animate(time){if(!running)return;const tag=$('#animate-axis').value,a=axes.find(x=>x.tag===tag);const q=(1-Math.cos(phase+(time-start)*Math.PI/2500))/2;state[tag]=a.min+q*(a.max-a.min);render();frame=requestAnimationFrame(animate)}
$('#play').addEventListener('click',()=>{if(running){stop();return}if(motion.matches){$('#motion-note').hidden=false;$('#motion-note').textContent=messages.reduced;return}const a=axes.find(x=>x.tag===$('#animate-axis').value);restore={...state};phase=Math.acos(1-2*Math.max(0,Math.min(1,(state[a.tag]-a.min)/(a.max-a.min))));start=performance.now();running=true;$('#sample').setAttribute('data-live','');$('#play').textContent=messages.stop;$('#play').setAttribute('aria-pressed','true');frame=requestAnimationFrame(animate)});
$('#animate-axis').addEventListener('change',stop);
function reduced(){if(motion.matches)stop();$('#motion-note').hidden=!motion.matches;$('#motion-note').textContent=motion.matches?messages.reduced:''}
motion.addEventListener('change',reduced);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop()});
$('#sample-input').addEventListener('input',()=>{$('#sample').textContent=$('#sample-input').value||' '});
$('#preview-size').addEventListener('input',()=>{$('#sample').style.fontSize=$('#preview-size').value+'px';$('#size-value').textContent=$('#preview-size').value+' px'});
const presets={brand:defaults,light:{...defaults,wght:500},wide:{...defaults,wdth:140},motion:{...defaults,wght:820,wdth:115,slnt:-12,ROND:45}};
document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>{stop();Object.assign(state,presets[b.dataset.preset]);clearPresets();b.setAttribute('aria-pressed','true');render()}));
$('#reset').addEventListener('click',()=>{stop();Object.assign(state,defaults);clearPresets();$('[data-preset=brand]').setAttribute('aria-pressed','true');render()});
$('#copy-css').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('#css-code').textContent);$('#copy-status').textContent=messages.copied}catch(e){const range=document.createRange();range.selectNodeContents($('#css-code'));const selection=getSelection();selection.removeAllRanges();selection.addRange(range);$('#copy-status').textContent=messages.copy_fallback}});
const groups={latin:'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',numbers:'0123456789!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~€£¥©®™⇒−–—‘’“”„…•■ΛΞ',extended:'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿĀāĂăĄąĆćČčĎďĐđĒēĖėĘęĚěĞğİıŁłŃńŇňŌōŐőŒœŔŕŘřŚśŠšŤťŪūŮůŰűŲųŸŹźŻżŽžẞ'};
function showGroup(group){$('#glyph-grid').replaceChildren();for(const char of groups[group]){const b=document.createElement('button');b.type='button';b.textContent=char;b.setAttribute('aria-label',char+' U+'+char.codePointAt(0).toString(16).toUpperCase().padStart(4,'0'));b.addEventListener('click',()=>{$('#selected-glyph').textContent=char;$('#glyph-code').textContent='U+'+char.codePointAt(0).toString(16).toUpperCase().padStart(4,'0')});$('#glyph-grid').append(b)}}
document.querySelectorAll('[data-group]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-group]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));showGroup(b.dataset.group)}));
try{const saved=JSON.parse(sessionStorage.getItem('lk-nova-specimen'));if(saved){for(const a of axes){const value=saved.axes?.[a.tag];if(Number.isFinite(value)&&value>=a.min&&value<=a.max)state[a.tag]=value}if(typeof saved.text==='string'){$('#sample-input').value=saved.text.slice(0,240);$('#sample').textContent=$('#sample-input').value||' '}const size=Number(saved.size);if(size>=32&&size<=200){$('#preview-size').value=size;$('#sample').style.fontSize=size+'px';$('#size-value').textContent=size+' px'}clearPresets();for(const button of document.querySelectorAll('[data-preset]')){if(axes.every(a=>state[a.tag]===presets[button.dataset.preset][a.tag]))button.setAttribute('aria-pressed','true')}}}catch(e){}
render();reduced();showGroup('latin');

// Edit in the final typeface and position, with the source field kept for persistence.
$('#sample').addEventListener('input',()=>{const text=$('#sample').innerText.replace(/\r/g,'');$('#sample-input').value=text.slice(0,240);if(text.length>240)$('#sample').textContent=text.slice(0,240)});
const presetGroup=document.querySelector('.presets');
const indicator=document.createElement('span');indicator.className='preset-indicator';indicator.setAttribute('aria-hidden','true');presetGroup.prepend(indicator);
function updatePresetIndicator(){const group=document.querySelector('.presets'),mark=group?.querySelector('.preset-indicator'),active=group?.querySelector('[aria-pressed=true]');if(!mark||group.dataset.dragging)return;mark.hidden=!active;if(active){mark.style.width=active.offsetWidth+'px';mark.style.height=active.offsetHeight+'px';mark.style.transform='translate('+active.offsetLeft+'px,'+active.offsetTop+'px)'}}
new ResizeObserver(updatePresetIndicator).observe(presetGroup);updatePresetIndicator();
const menu=document.querySelector('.language-options');
languagePicker.addEventListener('toggle',()=>{if(!languagePicker.open)return;menu.style.removeProperty('left');menu.style.removeProperty('right');menu.style.removeProperty('top');menu.style.removeProperty('bottom');const bounds=menu.getBoundingClientRect(),trigger=languagePicker.getBoundingClientRect();if(bounds.left<12){menu.style.left='0';menu.style.right='auto'}if(bounds.bottom>innerHeight-12&&trigger.top>bounds.height+12){menu.style.top='auto';menu.style.bottom='calc(100% + 8px)';menu.style.transformOrigin='bottom right'}});
languagePicker.querySelector('summary').addEventListener('keydown',event=>{if(event.key==='ArrowDown'){event.preventDefault();languagePicker.open=true;requestAnimationFrame(()=>menu.querySelector('[aria-current=true],button').focus())}});
menu.addEventListener('keydown',event=>{const buttons=[...menu.querySelectorAll('button')],index=buttons.indexOf(document.activeElement);if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus()}});

for(const slider of document.querySelectorAll('input[type=range]')){slider.addEventListener('pointerdown',()=>$('#sample').setAttribute('data-live',''));slider.addEventListener('keydown',()=>$('#sample').setAttribute('data-live',''));slider.addEventListener('keyup',()=>{if(!running)$('#sample').removeAttribute('data-live')})}
for(const event of ['pointerup','pointercancel'])document.addEventListener(event,()=>{if(!running)$('#sample').removeAttribute('data-live')});

const presetButtons=[...presetGroup.querySelectorAll('[data-preset]')];
const hoverIndicator=document.createElement('span');hoverIndicator.className='preset-hover';hoverIndicator.hidden=true;hoverIndicator.setAttribute('aria-hidden','true');presetGroup.prepend(hoverIndicator);
function previewPreset(button){if(presetGroup.dataset.dragging)button=null;hoverIndicator.hidden=!button;if(button){hoverIndicator.style.width=button.offsetWidth+'px';hoverIndicator.style.height=button.offsetHeight+'px';hoverIndicator.style.transform='translate('+button.offsetLeft+'px,'+button.offsetTop+'px)'}}
for(const button of presetButtons){button.addEventListener('pointerenter',event=>{if(event.pointerType==='mouse'&&!presetGroup.dataset.dragging)previewPreset(button)});button.addEventListener('focus',()=>previewPreset(button));button.addEventListener('blur',()=>previewPreset(null))}
presetGroup.addEventListener('pointerleave',()=>previewPreset(null));
let presetDrag=null,suppressPresetClick=false;
function nearestPreset(x){return presetButtons.reduce((best,button)=>Math.abs(x-(button.getBoundingClientRect().left+button.offsetWidth/2))<Math.abs(x-(best.getBoundingClientRect().left+best.offsetWidth/2))?button:best)}
presetGroup.addEventListener('pointerdown',event=>{if(event.button!==0)return;presetDrag={id:event.pointerId,x:event.clientX,y:event.clientY,dragging:false};previewPreset(null)});
presetGroup.addEventListener('pointermove',event=>{if(!presetDrag||event.pointerId!==presetDrag.id)return;const dx=event.clientX-presetDrag.x,dy=event.clientY-presetDrag.y;if(!presetDrag.dragging){if(Math.abs(dy)>8&&Math.abs(dy)>Math.abs(dx)){presetDrag=null;return}if(Math.abs(dx)<8)return;presetDrag.dragging=true;previewPreset(null);presetGroup.dataset.dragging='true';presetGroup.setPointerCapture(event.pointerId)}event.preventDefault();const button=nearestPreset(event.clientX),bounds=presetGroup.getBoundingClientRect();indicator.hidden=false;indicator.style.width=button.offsetWidth+'px';indicator.style.height=button.offsetHeight+'px';const x=Math.max(presetButtons[0].offsetLeft,Math.min(presetButtons.at(-1).offsetLeft,event.clientX-bounds.left-button.offsetWidth/2));indicator.style.transform='translate('+x+'px,'+button.offsetTop+'px)'});
function finishPresetDrag(event,cancelled){if(!presetDrag||event.pointerId!==presetDrag.id)return;const dragged=presetDrag.dragging;presetDrag=null;delete presetGroup.dataset.dragging;if(dragged){suppressPresetClick=true;if(!cancelled)nearestPreset(event.clientX).click();updatePresetIndicator();setTimeout(()=>{suppressPresetClick=false},0)}if(presetGroup.hasPointerCapture(event.pointerId))presetGroup.releasePointerCapture(event.pointerId)}
presetGroup.addEventListener('pointerup',event=>finishPresetDrag(event,false));presetGroup.addEventListener('pointercancel',event=>finishPresetDrag(event,true));presetGroup.addEventListener('lostpointercapture',event=>finishPresetDrag(event,true));
presetGroup.addEventListener('click',event=>{if(suppressPresetClick&&event.isTrusted){event.preventDefault();event.stopImmediatePropagation()}},true);

const magneticMedia=matchMedia('(hover: hover) and (pointer: fine)');
const magneticTargets=[...document.querySelectorAll('a.button[download][href$="LK-Nova-1.0.zip"]')];
for(const el of magneticTargets)el.classList.add('magnetic-target');
let magneticFrame=0,magneticPointer=null;
function resetMagnets(){magneticPointer=null;cancelAnimationFrame(magneticFrame);magneticFrame=0;for(const el of magneticTargets){el.style.removeProperty('--mag-x');el.style.removeProperty('--mag-y')}}
function updateMagnets(){magneticFrame=0;if(!magneticPointer||motion.matches||!magneticMedia.matches)return;for(const el of magneticTargets){if(!el.getClientRects().length)continue;const box=el.getBoundingClientRect(),style=getComputedStyle(el),offset=style.translate.split(' ');const left=box.left-(parseFloat(offset[0])||0),top=box.top-(parseFloat(offset[1])||0);const px=magneticPointer.x,py=magneticPointer.y,dx=px-(left+box.width/2),dy=py-(top+box.height/2);const distance=Math.hypot(Math.max(left-px,0,px-left-box.width),Math.max(top-py,0,py-top-box.height));const strength=Math.max(0,1-distance/48);const enabled=!(el===presetGroup&&presetDrag);el.style.setProperty('--mag-x',(enabled?Math.max(-4,Math.min(4,dx*.06))*strength:0)+'px');el.style.setProperty('--mag-y',(enabled?Math.max(-4,Math.min(4,dy*.06))*strength:0)+'px')}}
document.addEventListener('pointermove',event=>{if(event.pointerType!=='mouse'||event.buttons||motion.matches||!magneticMedia.matches){resetMagnets();return}magneticPointer={x:event.clientX,y:event.clientY};if(!magneticFrame)magneticFrame=requestAnimationFrame(updateMagnets)},{passive:true});
document.addEventListener('pointerdown',resetMagnets,{passive:true});document.documentElement.addEventListener('pointerleave',resetMagnets);window.addEventListener('blur',resetMagnets);window.addEventListener('scroll',resetMagnets,{passive:true});motion.addEventListener('change',resetMagnets);magneticMedia.addEventListener('change',resetMagnets);
