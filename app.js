const categories = [
  ['face','얼굴 · 메이크업','◉'],['hair','헤어','⌇'],['top','상의','♢'],['bottom','하의','▽'],['shoes','신발','⌁'],
  ['accessory','악세사리','✦'],['quality','화질','▦'],['place','장소','⌂'],['pose','자세','人'],['composition','구도','⊞']
];
const seedPrompts = [
  {id:'seed-1',category:'face',title:'내추럴 글로우',prompt:'natural dewy skin, subtle peach blush, softly defined brows, glossy nude lips, minimal clean makeup',tone:'linear-gradient(135deg,#d6b6a2,#81665d)'},
  {id:'seed-2',category:'face',title:'시네마틱 레드 립',prompt:'classic matte red lips, porcelain skin, subtle winged eyeliner, cinematic beauty look',tone:'linear-gradient(135deg,#983f3d,#d0a28e)'},
  {id:'seed-3',category:'face',title:'소프트 코랄 메이크업',prompt:'soft coral eye shadow, warm peachy cheeks, luminous skin, delicate natural freckles',tone:'linear-gradient(135deg,#e7b49e,#b9756e)'},
  {id:'seed-4',category:'hair',title:'내추럴 롱 웨이브',prompt:'long natural waves, soft layers framing the face, healthy glossy dark brown hair',tone:'linear-gradient(135deg,#5d4b42,#ba9b84)'},
  {id:'seed-5',category:'quality',title:'에디토리얼 필름',prompt:'high-end fashion editorial, subtle 35mm film grain, rich tonal range, crisp fine details',tone:'linear-gradient(135deg,#37444b,#b5aa95)'},
  {id:'seed-6',category:'place',title:'늦은 오후의 스튜디오',prompt:'minimal sunlit studio, warm late afternoon light, textured plaster wall, quiet atmosphere',tone:'linear-gradient(135deg,#d9b77e,#f0ded0)'}
];
let prompts = [], selected = {}, activeCategory = 'face', pendingImages = [];
const $ = selector => document.querySelector(selector);
const dbPromise = new Promise((resolve,reject)=>{const req=indexedDB.open('prompt-atelier',1);req.onupgradeneeded=()=>req.result.createObjectStore('data');req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)});
async function dbGet(key){const db=await dbPromise;return new Promise((resolve,reject)=>{const r=db.transaction('data').objectStore('data').get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
async function dbSet(key,value){const db=await dbPromise;return new Promise((resolve,reject)=>{const tx=db.transaction('data','readwrite');tx.objectStore('data').put(value,key);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)})}
function escapeHtml(value){return value.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function renderCategories(){
  $('#categoryList').innerHTML=categories.map(([id,name,icon])=>`<button class="category-button ${activeCategory===id?'active':''}" data-category="${id}"><span class="category-icon">${icon}</span><span class="category-name">${name}</span><span class="category-num">${prompts.filter(p=>p.category===id).length}</span></button>`).join('');
  $('#activeCategory').textContent=categories.find(c=>c[0]===activeCategory)[1];
  $('#libraryCount').textContent=`${prompts.length} saved`;
}
function renderCards(){
  const query=$('#searchInput').value.trim().toLowerCase();
  const shown=prompts.filter(p=>p.category===activeCategory && (!query || `${p.title} ${p.prompt}`.toLowerCase().includes(query)));
  $('#emptyState').hidden=shown.length>0;
  $('#promptGrid').innerHTML=shown.map(p=>`<article class="prompt-card ${selected[p.category]===p.id?'selected':''}" data-id="${p.id}" tabindex="0">
    <div class="card-image">${p.images?.[0]?`<img src="${p.images[0]}" alt="${escapeHtml(p.title)} 레퍼런스" />`:`<div class="placeholder-art" style="background:${p.tone||'linear-gradient(135deg,#bca798,#6b625d)'}">${p.title.charAt(0)}</div>`}${p.images?.length>1?`<span class="card-badge">+${p.images.length-1}</span>`:''}</div>
    <button class="delete-card" data-delete="${p.id}" aria-label="삭제">×</button><div class="card-body"><h3>${escapeHtml(p.title)}</h3><p>${escapeHtml(p.prompt)}</p></div></article>`).join('');
}
function renderSelections(){
  $('#selectionList').innerHTML=categories.map(([id,name])=>{const p=prompts.find(item=>item.id===selected[id]);return `<div class="selection-row ${p?'':'empty'}"><span class="selection-category">${name.split(' · ')[0]}</span><span class="selection-value">${p?escapeHtml(p.title):'선택 안 함'}</span>${p?`<button class="remove-selection" data-remove="${id}">×</button>`:'<span></span>'}</div>`}).join('');
  const combined=categories.map(([id])=>prompts.find(p=>p.id===selected[id])?.prompt).filter(Boolean).join(', ');
  $('#combinedPrompt').textContent=combined||'카드를 선택하면 이곳에 조합된 프롬프트가 표시됩니다.';
  $('#charCount').textContent=`${combined.length} chars`;
}
function render(){renderCategories();renderCards();renderSelections()}
async function persist(){await dbSet('prompts',prompts)}
function showToast(message){const toast=$('#toast');toast.textContent=message;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1800)}
function openDialog(){pendingImages=[];$('#promptForm').reset();$('#formCategory').value=activeCategory;$('#imagePreview').innerHTML='';$('#promptDialog').showModal()}
$('#categoryList').addEventListener('click',e=>{const button=e.target.closest('[data-category]');if(!button)return;activeCategory=button.dataset.category;render()});
$('#promptGrid').addEventListener('click',async e=>{const del=e.target.closest('[data-delete]');if(del){e.stopPropagation();if(!confirm('이 프롬프트를 삭제할까요?'))return;prompts=prompts.filter(p=>p.id!==del.dataset.delete);Object.keys(selected).forEach(k=>{if(selected[k]===del.dataset.delete)delete selected[k]});await persist();render();showToast('프롬프트를 삭제했어요');return}const card=e.target.closest('[data-id]');if(!card)return;const p=prompts.find(x=>x.id===card.dataset.id);selected[p.category]=selected[p.category]===p.id?undefined:p.id;renderCards();renderSelections()});
$('#selectionList').addEventListener('click',e=>{const b=e.target.closest('[data-remove]');if(b){delete selected[b.dataset.remove];render()}});
$('#searchInput').addEventListener('input',renderCards);
$('#addPromptButton').addEventListener('click',openDialog);$('#emptyAddButton').addEventListener('click',openDialog);
$('#closeDialog').addEventListener('click',()=>$('#promptDialog').close());$('#cancelDialog').addEventListener('click',()=>$('#promptDialog').close());
$('#formImages').addEventListener('change',async e=>{const files=[...e.target.files].slice(0,3);if([...e.target.files].length>3)showToast('이미지는 최대 3장까지 저장할 수 있어요');pendingImages=[];for(const file of files){if(file.size>2*1024*1024){showToast(`${file.name}: 2MB를 초과했어요`);continue}pendingImages.push(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsDataURL(file)}))}$('#imagePreview').innerHTML=pendingImages.map(src=>`<img src="${src}" alt="업로드 미리보기" />`).join('')});
$('#promptForm').addEventListener('submit',async e=>{e.preventDefault();prompts.unshift({id:crypto.randomUUID(),category:$('#formCategory').value,title:$('#formTitle').value.trim(),prompt:$('#formPrompt').value.trim(),images:pendingImages});activeCategory=$('#formCategory').value;await persist();$('#promptDialog').close();render();showToast('새 프롬프트를 저장했어요')});
$('#clearButton').addEventListener('click',()=>{selected={};render();showToast('선택을 모두 비웠어요')});
$('#copyButton').addEventListener('click',async()=>{const text=categories.map(([id])=>prompts.find(p=>p.id===selected[id])?.prompt).filter(Boolean).join(', ');if(!text){showToast('먼저 프롬프트를 선택해 주세요');return}await navigator.clipboard.writeText(text);showToast('클립보드에 복사했어요')});
$('#themeButton').addEventListener('click',()=>{document.body.classList.toggle('dark');localStorage.setItem('theme',document.body.classList.contains('dark')?'dark':'light')});
async function init(){prompts=await dbGet('prompts')||seedPrompts;if(localStorage.getItem('theme')==='dark')document.body.classList.add('dark');$('#formCategory').innerHTML=categories.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');render()}
init().catch(()=>{prompts=seedPrompts;render();showToast('저장소를 불러오지 못했어요')});
