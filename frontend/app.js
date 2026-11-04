/* The infrastructure supplies config.js; it never belongs to the release ZIP. */
const config = window.TICTACTEST;
const frame = document.querySelector('#terminal');
async function start() {
  if (!config?.consoleUrl) throw Error('Infrastruktur-Konfiguration config.js fehlt.');
  const consoleUrl = new URL(config.consoleUrl, location.href);
  frame.src = consoleUrl.href;
  const backendUrl = config.backendVersionUrl || new URL('/backend-version.json', consoleUrl);
  const [backend, frontend] = await Promise.all([
    fetch(backendUrl, {cache: 'no-store'}).then(r => {if (!r.ok) throw Error('Backend nicht erreichbar'); return r.json();}),
    fetch('version.json', {cache: 'no-store'}).then(r => {if (!r.ok) throw Error('Frontend-Version fehlt'); return r.json();})
  ]);
  document.querySelector('#versions').textContent = `Backend ${backend.version} · Frontend ${frontend.version}`;
}
document.querySelector('#restart').onclick = () => {frame.src = new URL(config.consoleUrl, location.href).href;};
start().catch(e => {document.querySelector('#versions').textContent = e.message;});
