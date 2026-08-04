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
let prompts = [], selected = {}, activeCategory = 'face', pendingImages = [], editingId = null;
const $ = selector => document.querySelector(selector);
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
    <div class="card-actions"><button class="edit-card" data-edit="${p.id}" aria-label="수정">✎</button><button class="delete-card" data-delete="${p.id}" aria-label="삭제">×</button></div><div class="card-body"><h3>${escapeHtml(p.title)}</h3></div></article>`).join('');
}
function buildCombinedPrompt(){
  return categories.map(([id,name])=>{
    const item=prompts.find(prompt=>prompt.id===selected[id]);
    return item?`[${name}]\n${item.prompt}`:'';
  }).filter(Boolean).join('\n\n');
}
function renderSelections(){
  $('#selectionList').innerHTML=categories.map(([id,name])=>{const p=prompts.find(item=>item.id===selected[id]);return `<div class="selection-row ${p?'':'empty'}"><span class="selection-category">${name.split(' · ')[0]}</span><span class="selection-value">${p?escapeHtml(p.title):'선택 안 함'}</span>${p?`<button class="remove-selection" data-remove="${id}">×</button>`:'<span></span>'}</div>`}).join('');
  const combined=buildCombinedPrompt();
  $('#combinedPrompt').textContent=combined||'카드를 선택하면 이곳에 조합된 프롬프트가 표시됩니다.';
  $('#charCount').textContent=`${combined.length} chars`;
}
function render(){renderCategories();renderCards();renderSelections()}
async function persist(){
  const response=await fetch('/api/prompts',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(prompts)});
  if(!response.ok)throw new Error((await response.json()).error||'server save failed');
  prompts=await response.json();
}
function showToast(message){const toast=$('#toast');toast.textContent=message;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1800)}
function renderImagePreview(){
  $('#imagePreview').innerHTML=pendingImages.map((src,index)=>`<div class="preview-item"><img src="${src}" alt="레퍼런스 미리보기" /><button type="button" data-remove-image="${index}" aria-label="사진 삭제">×</button></div>`).join('');
}
function openDialog(prompt=null){
  editingId=prompt?.id||null;
  pendingImages=[...(prompt?.images||[])];
  $('#promptForm').reset();
  $('#formCategory').value=prompt?.category||activeCategory;
  $('#formTitle').value=prompt?.title||'';
  $('#formPrompt').value=prompt?.prompt||'';
  $('#dialogEyebrow').textContent=prompt?'EDIT LIBRARY ITEM':'ADD TO LIBRARY';
  $('#dialogTitle').textContent=prompt?'프롬프트 수정':'새 프롬프트 저장';
  $('#savePromptButton').textContent=prompt?'변경사항 저장':'라이브러리에 저장';
  renderImagePreview();
  $('#promptDialog').showModal();
}
$('#categoryList').addEventListener('click',e=>{const button=e.target.closest('[data-category]');if(!button)return;activeCategory=button.dataset.category;render()});
$('#promptGrid').addEventListener('click',async e=>{
  const edit=e.target.closest('[data-edit]');
  if(edit){e.stopPropagation();openDialog(prompts.find(prompt=>prompt.id===edit.dataset.edit));return}
  const del=e.target.closest('[data-delete]');
  if(del){e.stopPropagation();if(!confirm('이 프롬프트를 삭제할까요?'))return;prompts=prompts.filter(p=>p.id!==del.dataset.delete);Object.keys(selected).forEach(k=>{if(selected[k]===del.dataset.delete)delete selected[k]});await persist();render();showToast('프롬프트를 삭제했어요');return}
  const card=e.target.closest('[data-id]');if(!card)return;const p=prompts.find(x=>x.id===card.dataset.id);selected[p.category]=selected[p.category]===p.id?undefined:p.id;renderCards();renderSelections();
});
$('#selectionList').addEventListener('click',e=>{const b=e.target.closest('[data-remove]');if(b){delete selected[b.dataset.remove];render()}});
$('#searchInput').addEventListener('input',renderCards);
$('#addPromptButton').addEventListener('click',openDialog);$('#emptyAddButton').addEventListener('click',openDialog);
$('#closeDialog').addEventListener('click',()=>$('#promptDialog').close());$('#cancelDialog').addEventListener('click',()=>$('#promptDialog').close());
$('#formImages').addEventListener('change',async e=>{
  const available=3-pendingImages.length;
  const files=[...e.target.files].slice(0,available);
  if([...e.target.files].length>available)showToast('이미지는 최대 3장까지 저장할 수 있어요');
  for(const file of files){if(file.size>10*1024*1024){showToast(`${file.name}: 10MB를 초과했어요`);continue}pendingImages.push(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsDataURL(file)}))}
  e.target.value='';renderImagePreview();
});
$('#imagePreview').addEventListener('click',e=>{const button=e.target.closest('[data-remove-image]');if(!button)return;pendingImages.splice(Number(button.dataset.removeImage),1);renderImagePreview()});
$('#promptForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const item={id:editingId||crypto.randomUUID(),category:$('#formCategory').value,title:$('#formTitle').value.trim(),prompt:$('#formPrompt').value.trim(),images:pendingImages};
  if(editingId){
    const previous=prompts.find(prompt=>prompt.id===editingId);
    if(previous&&previous.category!==item.category&&selected[previous.category]===editingId)delete selected[previous.category];
    prompts=prompts.map(prompt=>prompt.id===editingId?item:prompt);
  }else prompts.unshift(item);
  activeCategory=item.category;
  const wasEditing=Boolean(editingId);
  await persist();$('#promptDialog').close();render();showToast(wasEditing?'변경사항을 저장했어요':'새 프롬프트를 저장했어요');
});
$('#clearButton').addEventListener('click',()=>{selected={};render();showToast('선택을 모두 비웠어요')});
$('#copyButton').addEventListener('click',async()=>{const text=buildCombinedPrompt();if(!text){showToast('먼저 프롬프트를 선택해 주세요');return}await navigator.clipboard.writeText(text);showToast('클립보드에 복사했어요')});
$('#themeButton').addEventListener('click',()=>{document.body.classList.toggle('dark');localStorage.setItem('theme',document.body.classList.contains('dark')?'dark':'light')});
async function init(){
  const response=await fetch('/api/prompts');
  if(!response.ok)throw new Error('server load failed');
  const stored=await response.json();
  prompts=stored.length?stored:seedPrompts;
  if(!stored.length)await persist();
  if(localStorage.getItem('theme')==='dark')document.body.classList.add('dark');$('#formCategory').innerHTML=categories.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');render()}
init().catch(error=>{prompts=seedPrompts;$('#formCategory').innerHTML=categories.map(([id,name])=>`<option value="${id}">${name}</option>`).join('');render();showToast(`백엔드 오류: ${error.message}`)});
