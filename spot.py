import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Spot y la pelota", page_icon="🐶", layout="centered")

st.markdown(
    "<h1 style='text-align:center;margin-bottom:0'>🐶 Spot y la pelota</h1>"
    "<p style='text-align:center;opacity:.8'>Ayuda a Spot a perseguir su pelota. "
    "Salta los hidrantes, los conos y los gatos, pero no saltes cuando pase el cuervo.</p>",
    unsafe_allow_html=True,
)

GAME_HTML = r"""
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  html,body{margin:0;background:transparent;font-family:'Trebuchet MS',Verdana,sans-serif;}
  #wrap{max-width:800px;margin:0 auto;}
  canvas{width:100%;height:auto;display:block;border-radius:14px;touch-action:manipulation;cursor:pointer;outline:none;}
  canvas:focus-visible{box-shadow:0 0 0 3px #F4A51C;}
</style></head>
<body>
<div id="wrap"><canvas id="c" width="800" height="340" tabindex="0" aria-label="Juego de Spot. Pulsa espacio para saltar."></canvas></div>
<script>
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const W = 800, H = 340, GY = 280;           // GY = línea del suelo
const dpr = Math.min(window.devicePixelRatio || 1, 2);
cv.width = W * dpr; cv.height = H * dpr; ctx.scale(dpr, dpr);

// ---------------- Estado ----------------
let state = 'ready';                          // ready | play | over
let lives, score, best = 0, speed, dist, obs, nextSpawn, overTimer = 0, shake = 0, t = 0, popups = [];
const dog = { x: 130, y: GY, vy: 0, w: 58, h: 42, onGround: true, holding: false, holdT: 0, inv: 0, run: 0 };

const clouds = Array.from({length: 5}, (_, i) => ({ x: i * 190 + Math.random() * 80, y: 30 + Math.random() * 60, s: 0.7 + Math.random() * 0.6 }));
const trees  = Array.from({length: 6}, (_, i) => ({ x: i * 160 + Math.random() * 60, s: 0.8 + Math.random() * 0.5 }));

function reset() {
  lives = 3; score = 0; speed = 6; dist = 0; obs = []; nextSpawn = 500; popups = [];
  Object.assign(dog, { y: GY, vy: 0, onGround: true, holding: false, holdT: 0, inv: 0 });
}
reset();

// ---------------- Controles ----------------
function press() {
  if (state === 'ready') { reset(); state = 'play'; return; }
  if (state === 'over') { if (overTimer > 30) { reset(); state = 'play'; } return; }
  dog.holding = true;
  if (dog.onGround) { dog.vy = -11; dog.onGround = false; dog.holdT = 0; }
}
function release() { dog.holding = false; }

const JUMP_KEYS = ['Space', 'ArrowUp', 'KeyW'];
window.addEventListener('keydown', e => { if (JUMP_KEYS.includes(e.code)) { e.preventDefault(); if (!e.repeat) press(); } });
window.addEventListener('keyup',   e => { if (JUMP_KEYS.includes(e.code)) release(); });
cv.addEventListener('pointerdown', e => { e.preventDefault(); cv.focus(); press(); });
cv.addEventListener('pointerup', release);
cv.addEventListener('pointerleave', release);

// ---------------- Obstáculos ----------------
function spawn() {
  const r = Math.random();
  let type;
  if (score < 25)      type = r < 0.5 ? 'hydrant' : 'cone';
  else if (r < 0.28)   type = 'hydrant';
  else if (r < 0.48)   type = 'cone';
  else if (r < 0.74)   type = 'cat';
  else                 type = 'crow';

  const o = { type, x: W + 20, anim: 0 };
  if (type === 'hydrant') Object.assign(o, { w: 24, h: 36, mult: 1 });
  if (type === 'cone')    Object.assign(o, { w: 26, h: 30, mult: 1 });
  if (type === 'cat')     Object.assign(o, { w: 46, h: 30, mult: 1.45 });   // corre hacia Spot
  if (type === 'crow')    Object.assign(o, { w: 42, h: 22, mult: 1.3, base: 224 }); // vuela a la altura del salto
  o.y = GY;
  obs.push(o);
  nextSpawn = 260 + Math.random() * 260 + speed * 24 + (o.mult - 1) * 220;
}

function hit() {
  lives--; dog.inv = 100; shake = 14;
  popups.push({ text: '¡Auch!', x: dog.x + 30, y: dog.y - 60, life: 50 });
  if (lives <= 0) { state = 'over'; overTimer = 0; best = Math.max(best, score); }
}

function overlap(a, b) { return a.l < b.r && a.r > b.l && a.t < b.b && a.b > b.t; }

// ---------------- Actualización ----------------
function update(dt) {
  t += dt;
  if (shake > 0) shake -= dt;
  popups.forEach(p => { p.life -= dt; p.y -= 0.6 * dt; });
  popups = popups.filter(p => p.life > 0);

  if (state === 'over') {
    overTimer += dt;
    if (overTimer > 180) { reset(); state = 'play'; }   // reinicio automático a los ~3 s
    return;
  }
  if (state !== 'play') return;

  // Salto con altura variable: mantener pulsado = salto más alto
  if (!dog.onGround) {
    const boosting = dog.holding && dog.vy < 0 && dog.holdT < 14;
    if (dog.holding) dog.holdT += dt;
    dog.vy += (boosting ? 0.38 : 0.62) * dt;
    dog.y += dog.vy * dt;
    if (dog.y >= GY) { dog.y = GY; dog.vy = 0; dog.onGround = true; }
  }
  dog.run += speed * dt * 0.07;
  if (dog.inv > 0) dog.inv -= dt;

  speed = Math.min(13, speed + 0.0018 * dt);
  dist += speed * dt;
  score = Math.floor(dist / 25);

  nextSpawn -= speed * dt;
  if (nextSpawn <= 0) spawn();

  const dBox = { l: dog.x + 10, r: dog.x + dog.w - 4, t: dog.y - dog.h + 8, b: dog.y };
  for (const o of obs) {
    o.x -= speed * o.mult * dt;
    o.anim += dt;
    if (o.type === 'crow') o.y = o.base + Math.sin(o.anim * 0.09) * 5;
    const oBox = { l: o.x + 5, r: o.x + o.w - 5, t: o.y - o.h + 5, b: o.y };
    if (dog.inv <= 0 && state === 'play' && overlap(dBox, oBox)) hit();
  }
  obs = obs.filter(o => o.x > -80);

  clouds.forEach(c => { c.x -= speed * 0.12 * c.s * dt; if (c.x < -120) c.x = W + 40; });
  trees.forEach(tr => { tr.x -= speed * 0.45 * dt; if (tr.x < -80) tr.x = W + 60 + Math.random() * 80; });
}

// ---------------- Dibujo ----------------
function drawBackground() {
  const g = ctx.createLinearGradient(0, 0, 0, GY);
  g.addColorStop(0, '#7EC8EC'); g.addColorStop(1, '#DFF3FB');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

  ctx.fillStyle = '#FFE08A';
  ctx.beginPath(); ctx.arc(690, 60, 30, 0, Math.PI * 2); ctx.fill();

  ctx.fillStyle = 'rgba(255,255,255,.9)';
  clouds.forEach(c => {
    ctx.beginPath();
    ctx.arc(c.x, c.y, 16 * c.s, 0, Math.PI * 2);
    ctx.arc(c.x + 20 * c.s, c.y - 8 * c.s, 20 * c.s, 0, Math.PI * 2);
    ctx.arc(c.x + 42 * c.s, c.y, 15 * c.s, 0, Math.PI * 2);
    ctx.fill();
  });

  // colinas con parallax
  const off = (dist * 0.15) % 400;
  ctx.fillStyle = '#A8D58E';
  ctx.beginPath(); ctx.moveTo(0, GY);
  for (let x = 0; x <= W; x += 10) ctx.lineTo(x, GY - 55 - Math.sin((x + off) / 64) * 22);
  ctx.lineTo(W, GY); ctx.fill();

  trees.forEach(tr => {
    const s = tr.s;
    ctx.fillStyle = '#8A5A36'; ctx.fillRect(tr.x - 4 * s, GY - 55 * s, 8 * s, 55 * s);
    ctx.fillStyle = '#4E9A45';
    ctx.beginPath(); ctx.arc(tr.x, GY - 62 * s, 24 * s, 0, Math.PI * 2); ctx.arc(tr.x - 16 * s, GY - 50 * s, 16 * s, 0, Math.PI * 2); ctx.arc(tr.x + 16 * s, GY - 50 * s, 16 * s, 0, Math.PI * 2); ctx.fill();
  });

  // pasto y camino
  ctx.fillStyle = '#5FA64B'; ctx.fillRect(0, GY, W, 10);
  ctx.fillStyle = '#D9B67C'; ctx.fillRect(0, GY + 10, W, H - GY - 10);
  ctx.fillStyle = '#C49D63';
  const doff = dist % 60;
  for (let x = -doff; x < W; x += 60) ctx.fillRect(x, GY + 26, 26, 4);
}

function drawBall() {
  const bx = dog.x + 215 + Math.sin(t * 0.018) * 25;
  const bounce = Math.abs(Math.sin(t * 0.11)) * 42;
  const by = GY - 11 - bounce;
  ctx.fillStyle = 'rgba(0,0,0,.15)';
  ctx.beginPath(); ctx.ellipse(bx, GY + 3, 11 - bounce * 0.12, 3, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#D6EE3E';
  ctx.beginPath(); ctx.arc(bx, by, 11, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(bx - 9, by, 8, -0.9, 0.9); ctx.stroke();
  ctx.beginPath(); ctx.arc(bx + 9, by, 8, Math.PI - 0.9, Math.PI + 0.9); ctx.stroke();
}

function drawDog() {
  if (state === 'play' && dog.inv > 0 && Math.floor(dog.inv / 6) % 2 === 0) return;   // parpadeo tras un golpe
  const x = dog.x, y = dog.y;
  const line = '#3B2A1C', white = '#FBF8F1', brown = '#A0612B';
  ctx.lineWidth = 2; ctx.strokeStyle = line; ctx.lineCap = 'round';

  // sombra
  ctx.fillStyle = 'rgba(0,0,0,.15)';
  const sh = Math.max(0.4, 1 - (GY - y) / 160);
  ctx.beginPath(); ctx.ellipse(x + 30, GY + 3, 26 * sh, 4 * sh, 0, 0, Math.PI * 2); ctx.fill();

  // patas
  const sw = dog.onGround ? Math.sin(dog.run) * 7 : 0;
  ctx.lineWidth = 5; ctx.strokeStyle = white;
  const legs = dog.onGround
    ? [[x + 14, x + 14 + sw], [x + 20, x + 20 - sw], [x + 38, x + 38 - sw], [x + 44, x + 44 + sw]]
    : [[x + 14, x + 6], [x + 20, x + 12], [x + 38, x + 48], [x + 44, x + 54]];
  legs.forEach(([top, foot]) => {
    ctx.beginPath(); ctx.moveTo(top, y - 18); ctx.lineTo(foot, dog.onGround ? y - 1 : y - 8); ctx.stroke();
  });
  ctx.lineWidth = 2; ctx.strokeStyle = line;

  // cola que se mueve
  const wag = Math.sin(t * 0.4) * 6;
  ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(x + 8, y - 30); ctx.quadraticCurveTo(x - 4, y - 38, x - 2 + wag * 0.3, y - 48 + wag * 0.5); ctx.stroke();
  ctx.lineWidth = 2;

  // cuerpo
  ctx.fillStyle = white;
  ctx.beginPath(); ctx.roundRect(x + 6, y - 38, 44, 22, 11); ctx.fill(); ctx.stroke();
  // mancha café en el lomo
  ctx.fillStyle = brown;
  ctx.beginPath(); ctx.ellipse(x + 22, y - 31, 10, 6, -0.2, 0, Math.PI * 2); ctx.fill();
  // collar
  ctx.fillStyle = '#2E7BD6'; ctx.fillRect(x + 45, y - 40, 4, 16);

  // cabeza
  const hx = x + 56, hy = y - 42;
  ctx.fillStyle = white;
  ctx.beginPath(); ctx.arc(hx, hy, 12, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  // hocico
  ctx.beginPath(); ctx.roundRect(hx + 6, hy - 1, 13, 10, 5); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#1C1410'; ctx.beginPath(); ctx.arc(hx + 18, hy + 2, 2.6, 0, Math.PI * 2); ctx.fill();
  // mancha café en el ojo y oreja doblada
  ctx.fillStyle = brown;
  ctx.beginPath(); ctx.ellipse(hx + 2, hy - 4, 6, 5, 0, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(hx - 8, hy - 10); ctx.quadraticCurveTo(hx - 18, hy - 6, hx - 14, hy + 6); ctx.lineTo(hx - 6, hy - 2); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#1C1410'; ctx.beginPath(); ctx.arc(hx + 3, hy - 4, 2, 0, Math.PI * 2); ctx.fill();
  // lengua cuando corre
  if (dog.onGround) { ctx.fillStyle = '#E86A7A'; ctx.beginPath(); ctx.roundRect(hx + 9, hy + 8, 5, 6, 2); ctx.fill(); }
}

function drawObstacle(o) {
  const x = o.x, y = o.y;
  ctx.lineWidth = 2; ctx.strokeStyle = '#2B2B2B';
  if (o.type === 'hydrant') {
    ctx.fillStyle = '#D8423A';
    ctx.beginPath(); ctx.roundRect(x + 3, y - 30, 18, 30, 3); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.arc(x + 12, y - 30, 9, Math.PI, 0); ctx.fill(); ctx.stroke();
    ctx.fillRect(x - 1, y - 20, 26, 6); ctx.strokeRect(x - 1, y - 20, 26, 6);
    ctx.fillStyle = '#F3F3F3'; ctx.fillRect(x + 3, y - 8, 18, 3);
  }
  if (o.type === 'cone') {
    ctx.fillStyle = '#F07F1F';
    ctx.beginPath(); ctx.moveTo(x + 13, y - 30); ctx.lineTo(x + 24, y - 3); ctx.lineTo(x + 2, y - 3); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.fillRect(x + 8, y - 17, 10, 4);
    ctx.fillStyle = '#F07F1F'; ctx.fillRect(x - 1, y - 4, 28, 4); ctx.strokeRect(x - 1, y - 4, 28, 4);
  }
  if (o.type === 'cat') {
    const step = Math.sin(o.anim * 0.45) * 5;
    ctx.fillStyle = '#3D3A45'; ctx.strokeStyle = '#1D1B22';
    ctx.lineWidth = 4;
    [[x + 12, step], [x + 18, -step], [x + 30, -step], [x + 36, step]].forEach(([lx, s]) => { ctx.beginPath(); ctx.moveTo(lx, y - 12); ctx.lineTo(lx + s, y - 1); ctx.stroke(); });
    ctx.beginPath(); ctx.moveTo(x + 40, y - 18); ctx.quadraticCurveTo(x + 54, y - 22, x + 50, y - 36); ctx.stroke();
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(x + 26, y - 17, 17, 8, 0, Math.PI, 0); ctx.lineTo(x + 43, y - 12); ctx.lineTo(x + 9, y - 12); ctx.closePath(); ctx.fill(); // lomo arqueado
    ctx.beginPath(); ctx.arc(x + 8, y - 20, 9, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x + 1, y - 25); ctx.lineTo(x + 3, y - 34); ctx.lineTo(x + 8, y - 27); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x + 9, y - 27); ctx.lineTo(x + 14, y - 34); ctx.lineTo(x + 15, y - 24); ctx.fill();
    ctx.fillStyle = '#F6D23B';
    ctx.beginPath(); ctx.arc(x + 4, y - 21, 2.3, 0, Math.PI * 2); ctx.arc(x + 11, y - 21, 2.3, 0, Math.PI * 2); ctx.fill();
  }
  if (o.type === 'crow') {
    ctx.fillStyle = 'rgba(0,0,0,.12)';
    ctx.beginPath(); ctx.ellipse(x + 21, GY + 3, 16, 3, 0, 0, Math.PI * 2); ctx.fill();
    const flap = Math.sin(o.anim * 0.35) * 12;
    ctx.fillStyle = '#1E1E26';
    ctx.beginPath(); ctx.ellipse(x + 22, y - 11, 16, 8, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(x + 16, y - 14); ctx.lineTo(x + 30, y - 22 - flap); ctx.lineTo(x + 34, y - 12); ctx.fill();
    ctx.beginPath(); ctx.arc(x + 8, y - 15, 7, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#F2A33A';
    ctx.beginPath(); ctx.moveTo(x + 2, y - 16); ctx.lineTo(x - 7, y - 13); ctx.lineTo(x + 2, y - 11); ctx.fill();
    ctx.fillStyle = '#E4383A'; ctx.beginPath(); ctx.arc(x + 6, y - 16, 1.8, 0, Math.PI * 2); ctx.fill();
  }
}

function drawHUD() {
  ctx.font = '22px sans-serif'; ctx.textBaseline = 'top'; ctx.textAlign = 'left';
  for (let i = 0; i < 3; i++) ctx.fillText(i < lives ? '❤️' : '🤍', 16 + i * 30, 12);
  ctx.textAlign = 'right'; ctx.fillStyle = '#233A48'; ctx.font = 'bold 18px Trebuchet MS, sans-serif';
  ctx.fillText(`${score} m   Récord: ${best} m`, W - 16, 16);
  popups.forEach(p => { ctx.textAlign = 'center'; ctx.fillStyle = `rgba(200,40,40,${Math.min(1, p.life / 25)})`; ctx.font = 'bold 20px Trebuchet MS, sans-serif'; ctx.fillText(p.text, p.x, p.y); });
}

function panel(lines) {
  ctx.fillStyle = 'rgba(20,35,45,.72)';
  ctx.beginPath(); ctx.roundRect(W / 2 - 250, 70, 500, 44 + lines.length * 30, 16); ctx.fill();
  ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  lines.forEach((l, i) => {
    ctx.fillStyle = i === 0 ? '#FFD66B' : '#FFFFFF';
    ctx.font = i === 0 ? 'bold 30px Trebuchet MS, sans-serif' : '18px Trebuchet MS, sans-serif';
    ctx.fillText(l, W / 2, 90 + i * 32 + (i > 0 ? 8 : 0));
  });
}

function draw() {
  ctx.save();
  if (shake > 0) ctx.translate((Math.random() - 0.5) * shake, (Math.random() - 0.5) * shake);
  drawBackground();
  drawBall();
  obs.forEach(drawObstacle);
  drawDog();
  ctx.restore();
  drawHUD();

  if (state === 'ready') panel(['Spot y la pelota', 'Toca o pulsa Espacio para empezar', 'Mantén pulsado para saltar más alto', 'Salta hidrantes, conos y gatos. ¡Ojo con el cuervo!']);
  if (state === 'over') panel(['Se acabaron las vidas', `Spot corrió ${score} m`, `Reiniciando en ${Math.max(1, Math.ceil((180 - overTimer) / 60))}...  (toca para empezar ya)`]);
}

// ---------------- Bucle ----------------
let last = performance.now();
function loop(now) {
  const dt = Math.min(3, (now - last) / 16.67);
  last = now;
  update(dt);
  draw();
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
</script>
</body></html>
"""

components.html(GAME_HTML, height=320, scrolling=False)

st.caption("Controles: Espacio, flecha arriba o W en computadora; toca el juego en el celular.")
