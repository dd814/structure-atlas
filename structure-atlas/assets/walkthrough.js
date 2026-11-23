function mountWalkthrough(panel, plan, make, nodeButton) {
  const [, stepId, attemptId] = location.hash.slice(1).split('/');
  let step = plan.steps.find(item => item.id === stepId) || plan.steps.find(item => item.attempts.length) || plan.steps[0];
  let attempt = step.attempts.find(item => item.id === attemptId) || step.attempts.at(-1);
  const stages = make('nav', null, 'walkthrough-steps');
  stages.setAttribute('aria-label', '实跑步骤');
  const columns = make('div', null, 'walkthrough-grid');
  const detail = make('article');
  const practice = make('article');
  columns.append(detail, practice);
  panel.append(make('h2', plan.title), stages, columns);
  const buttons = plan.steps.map(item => {
    const button = make('button', item.title);
    button.type = 'button';
    button.addEventListener('click', () => { select(item.id); link(); });
    stages.append(button);
    return button;
  });

  function link() {
    const path = '#walkthrough/' + step.id + (attempt ? '/' + attempt.id : '');
    if (location.hash !== path) history.replaceState(null, '', path);
  }

  function select(id) {
    step = plan.steps.find(item => item.id === id);
    attempt = step.attempts.at(-1);
    draw();
  }

  function comments(run, stage) {
    const form = make('form');
    const input = make('textarea');
    input.id = 'walkthrough-note';
    input.rows = 3;
    input.maxLength = 2000;
    input.required = true;
    const label = make('label', '给这次运行写批注');
    label.htmlFor = input.id;
    const save = make('button', '保存批注');
    save.disabled = true;
    const status = make('p', '正在读取批注…', 'caption');
    status.setAttribute('role', 'status');
    const list = make('ul');
    const keys = {walkthrough_id:plan.id, step_id:stage.id, attempt_id:run.id,
      run_id:run.run_id, code_version:run.code_version, input_id:run.input_id};
    const url = '/feedback?' + new URLSearchParams(keys);
    let token;

    async function request(options) {
      const response = await fetch(url, options);
      if (!response.headers.get('Content-Type')?.includes('application/json')) throw Error('请通过本地图谱服务打开页面。');
      const data = await response.json();
      if (!response.ok) throw Error(data.error);
      list.replaceChildren(...data.notes.map(note => make('li', note.text)));
      return data;
    }

    request().then(data => {
      token = data.token;
      save.disabled = false;
      status.textContent = '批注保存在本机，并绑定这次运行。';
    }).catch(error => { status.textContent = error.message; });
    let submission;
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text || save.disabled) return;
      if (submission?.text !== text) submission = {id:crypto.randomUUID(), text};
      save.disabled = true;
      try {
        await request({method:'POST', headers:{'Content-Type':'application/json', 'X-Atlas-Token':token},
          body:JSON.stringify(submission)});
        input.value = '';
        submission = null;
        status.textContent = '已保存。回到 Agent 说「读批注」，即可从这次运行继续。';
      } catch (error) {
        status.textContent = error.message;
      } finally {
        save.disabled = false;
      }
    });
    form.append(label, input, save, status, list);
    return form;
  }

  function draw() {
    buttons.forEach((button, index) => button.setAttribute('aria-pressed', plan.steps[index] === step));
    const snapshot = attempt || step;
    const facts = make('dl');
    for (const [name, value] of [['代码位置', snapshot.source], ['输入', snapshot.input],
      ['跑前预期', snapshot.expected], ['建议核对', snapshot.advice]]) {
      if (value) facts.append(make('dt', name), make('dd', value));
    }
    detail.replaceChildren(make('h3', step.title), nodeButton(step.node), facts);
    practice.replaceChildren(make('h3', '实际结果'));
    if (!attempt) {
      practice.append(make('p', '这一步还没有实跑记录。'));
      return;
    }
    const history = make('select');
    history.id = 'walkthrough-run';
    const label = make('label', '查看哪次运行');
    label.htmlFor = history.id;
    for (const item of step.attempts) {
      const option = make('option', item.id + ' · ' + item.code_version.slice(0, 12));
      option.value = item.id;
      history.append(option);
    }
    history.value = attempt.id;
    history.addEventListener('change', () => {
      attempt = step.attempts.find(item => item.id === history.value);
      draw();
      link();
      detail.querySelector('select').focus();
    });
    const source = make('details');
    source.append(make('summary', '展开本次运行的代码'), make('pre', attempt.code));
    detail.append(label, history, source);
    if (attempt.change) detail.append(make('p', attempt.change, 'caption'));
    if (document.querySelector('meta[name="atlas-live"]')) detail.append(comments(attempt, step));
    else detail.append(make('p', '使用本地图谱服务打开，可按运行记录保存批注。', 'caption'));
    practice.append(make('p', attempt.result));
    if (attempt.output) practice.append(make('pre', attempt.output));
    if (attempt.preview_url) {
      const preview = make('a', '单独打开实跑页面');
      preview.href = attempt.preview_url;
      preview.target = '_blank';
      preview.rel = 'noopener';
      practice.append(preview);
      if (location.protocol !== 'file:' && new URL(preview.href).origin !== location.origin) {
        const frame = make('iframe');
        frame.title = '实跑预览 · ' + attempt.id;
        frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
        frame.src = preview.href;
        practice.append(frame);
      }
    }
    const ids = make('details', null, 'caption');
    ids.append(make('summary', '查看本次运行的标识'),
      make('p', '运行 ' + attempt.run_id), make('p', '代码 ' + attempt.code_version),
      make('p', '输入 ' + attempt.input_id));
    practice.append(ids);
  }
  draw();
  return {select, link};
}
