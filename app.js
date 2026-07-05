async function loadData(){
  const res = await fetch('results.json?ts=' + Date.now());
  const data = await res.json();
  const items = data.items || [];
  document.getElementById('updated').textContent = data.updated || '-';
  document.getElementById('summary').textContent = data.summary || 'データがありません。';
  const counts = {肯定:0, 中立:0, 否定:0};
  items.forEach(i => counts[i.sentiment] = (counts[i.sentiment] || 0) + 1);
  document.getElementById('total').textContent = items.length;
  document.getElementById('positive').textContent = counts.肯定 || 0;
  document.getElementById('neutral').textContent = counts.中立 || 0;
  document.getElementById('negative').textContent = counts.否定 || 0;

  const kw = document.getElementById('keywords');
  kw.innerHTML = '';
  (data.keywords || []).forEach(k => {
    const s = document.createElement('span'); s.textContent = k; kw.appendChild(s);
  });

  const render = () => {
    const q = document.getElementById('search').value.trim();
    const box = document.getElementById('items');
    box.innerHTML = '';
    items.filter(i => !q || JSON.stringify(i).includes(q)).forEach(i => {
      const div = document.createElement('div');
      div.className = 'item';
      div.innerHTML = `<a href="${i.link}" target="_blank" rel="noopener">${i.title}</a>
        <div class="meta"><span class="badge ${i.sentiment}">${i.sentiment}</span>${i.source || ''} / ${i.date || ''}</div>
        <p>${i.snippet || ''}</p>`;
        <p class="reason">判定理由：${i.sentiment_reason || i.reason || '理由なし'}</p>
      box.appendChild(div);
    });
  };
  document.getElementById('search').addEventListener('input', render);
  render();
}
loadData().catch(e => {
  document.getElementById('summary').textContent = 'データ読込に失敗しました。GitHub Actionsの実行後に再確認してください。';
});
