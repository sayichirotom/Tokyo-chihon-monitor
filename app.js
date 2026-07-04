const els = {
  status: document.getElementById('status'), total: document.getElementById('total'),
  positive: document.getElementById('positive'), neutral: document.getElementById('neutral'), negative: document.getElementById('negative'),
  summary: document.getElementById('summary'), keywords: document.getElementById('keywords'), items: document.getElementById('items'), filter: document.getElementById('filter'),
  bp: document.getElementById('bar-positive'), bn: document.getElementById('bar-neutral'), bg: document.getElementById('bar-negative')
};
let DATA = null;
function pct(n,total){ return total ? Math.round(n/total*100) : 0; }
function badge(sentiment){
  const label = sentiment === 'positive' ? '肯定' : sentiment === 'negative' ? '否定' : '中立';
  return `<span class="badge ${sentiment}">${label}</span>`;
}
function render(){
  const items = DATA.items || [];
  const q = (els.filter.value || '').toLowerCase();
  const filtered = items.filter(x => `${x.title} ${x.snippet} ${x.source}`.toLowerCase().includes(q));
  const counts = {positive:0, neutral:0, negative:0};
  items.forEach(x => counts[x.sentiment] = (counts[x.sentiment] || 0) + 1);
  els.status.textContent = `最終更新：${DATA.generated_at || '-'}`;
  els.total.textContent = items.length;
  els.positive.textContent = `${pct(counts.positive, items.length)}%`;
  els.neutral.textContent = `${pct(counts.neutral, items.length)}%`;
  els.negative.textContent = `${pct(counts.negative, items.length)}%`;
  els.bp.value = pct(counts.positive, items.length);
  els.bn.value = pct(counts.neutral, items.length);
  els.bg.value = pct(counts.negative, items.length);
  els.summary.textContent = DATA.summary || '収集結果を表示しています。';
  els.keywords.innerHTML = (DATA.keywords || []).map(k => `<span class="chip">${k}</span>`).join('');
  els.items.innerHTML = filtered.map(x => `<article class="item"><div class="meta">${badge(x.sentiment)}<span>${x.source}</span><span>${x.published || ''}</span></div><h3><a href="${x.url}" target="_blank" rel="noopener">${x.title}</a></h3><p>${x.snippet || ''}</p></article>`).join('') || '<p>該当なし</p>';
}
fetch('data/report.json', {cache:'no-store'}).then(r=>r.json()).then(d=>{DATA=d; render();}).catch(()=>{
  els.status.textContent='サンプル表示';
  DATA={generated_at:'未収集',summary:'まだ自動収集前です。GitHub Actionsを有効にすると毎日更新されます。',keywords:['東京地本','自衛隊','募集','航空学生'],items:[]}; render();
});
els.filter.addEventListener('input',()=> DATA && render());
