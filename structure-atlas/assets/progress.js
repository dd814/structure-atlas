function mountAtlasProgress({ panel, summary, checkpoints, title, label, openProgress, openNode }) {
  const latest = new Map();
  const states = { verified:'已验证', implemented:'已实现待验证', blocked:'受阻', planned:'待推进' };
  const element = (tag, text, className) => {
    const item = document.createElement(tag);
    if (text) item.textContent = text;
    if (className) item.className = className;
    return item;
  };
  const button = (text, click) => {
    const item = element('button', text, 'structure-progress-button');
    item.type = 'button';
    item.addEventListener('click', click);
    return item;
  };
  const describe = (checkpoint, change, name) => [
    `我正在查看《${title}》的项目进展。`,
    `更新：${checkpoint.date} · ${checkpoint.title}`,
    `涉及部件：${name}`,
    `状态：${states[change.status]}`,
    `目前情况：${change.note}`,
    change.evidence && `依据：${change.evidence}`,
    `我想继续讨论：${change.next || '根据目前情况，下一步应先验证或推进什么？'}`,
  ].filter(Boolean).join('\n');

  for (const checkpoint of [...checkpoints].reverse()) {
    const section = element('section', '', 'structure-progress-checkpoint');
    const date = element('time', checkpoint.date);
    date.dateTime = checkpoint.date;
    section.append(date, element('h3', checkpoint.title));
    for (const change of checkpoint.changes) {
      const name = label(change.node);
      const row = element('article', '', 'structure-progress-change');
      row.dataset.status = change.status;
      const heading = element('h4', `${name} · ${states[change.status]}`);
      heading.tabIndex = -1;
      row.append(heading, element('p', change.note));
      if (change.evidence) row.append(element('p', `依据 · ${change.evidence}`, 'structure-progress-meta'));
      if (change.next) row.append(element('p', `接下来 · ${change.next}`, 'structure-progress-meta'));
      const actions = element('div', '', 'structure-progress-actions');
      const feedback = element('span', '', 'structure-progress-meta');
      feedback.setAttribute('role', 'status');
      const fallback = element('textarea', '', 'structure-progress-context');
      fallback.readOnly = true;
      fallback.rows = 5;
      fallback.hidden = true;
      fallback.setAttribute('aria-label', '可手动复制的讨论上下文');
      actions.append(button('查看对应部件', () => openNode(change.node)), button('复制讨论上下文', async () => {
        const text = describe(checkpoint, change, name);
        try {
          await navigator.clipboard.writeText(text);
          fallback.hidden = true;
          feedback.textContent = '已复制，可粘贴到 Agent 对话。';
        } catch {
          fallback.value = text;
          fallback.hidden = false;
          fallback.focus();
          fallback.select();
          feedback.textContent = '请手动复制已选中的讨论文字。';
        }
      }), feedback);
      row.append(actions, fallback);
      section.append(row);
      if (!latest.has(change.node)) latest.set(change.node, { checkpoint, change, heading });
    }
    panel.append(section);
  }
  if (checkpoints.length && summary) {
    summary.textContent = `最近更新 · ${checkpoints.at(-1).date} · ${checkpoints.at(-1).title}`;
    summary.hidden = false;
  }

  return function latestNote(node) {
    const entry = latest.get(node);
    if (!entry) return null;
    const note = element('div', '', 'structure-progress-note');
    note.dataset.status = entry.change.status;
    note.append(element('strong', `${entry.checkpoint.date} · ${states[entry.change.status]}`),
      element('p', entry.change.note),
      button('看这条进展', () => {
        openProgress();
        entry.heading.focus({ preventScroll:true });
        entry.heading.scrollIntoView({ block:'nearest' });
      }));
    return note;
  };
}
