"use strict";

const { manifest, sheets } = JSON.parse(document.querySelector("#project-data").textContent);
const byId = id => document.getElementById(id);
const actions = [...document.querySelectorAll("[data-action]")];
const seek = byId("seek");
const play = byId("play");
const loop = byId("loop");
const speed = byId("speed");
const zoom = byId("zoom");
const compare = byId("compare");
const comparison = byId("secondary-action");
const guide = byId("guide");
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
const panes = [
  { canvas: byId("primary"), meta: byId("primary-meta") },
  { canvas: byId("secondary"), meta: byId("secondary-meta") },
];
const images = {};
const { width, height, anchor } = manifest.canvas;

for (const clip of Object.values(manifest.clips)) {
  clip.starts = [];
  clip.duration = 0;
  for (const frame of clip.frames) {
    clip.starts.push(clip.duration);
    clip.duration += frame.hold * manifest.tickMs;
  }
}

let active = "idle";
let time = 0;
let playing = !reducedMotion.matches;
let ready = false;
let request = null;
let lastTimestamp = null;
const first = () => manifest.clips[active];
const second = () => manifest.clips[comparison.value];
const duration = () => compare.checked ? Math.max(first().duration, second().duration) : first().duration;
const seconds = ms => (ms / 1000).toFixed(2) + " s";

function frameAt(clip, ms) {
  const next = clip.starts.findIndex(start => start > ms);
  return next < 0 ? clip.frames.length - 1 : next - 1;
}

function draw(pane, clip, index) {
  const holding = compare.checked && time >= clip.duration && clip.duration < duration();
  const { meta } = pane;
  const label = String(index + 1).padStart(2, "0") + " / " + clip.frames.length;
  if (meta.textContent !== (holding ? label + " · Hold" : label)) {
    meta.textContent = label;
    if (holding) {
      const status = document.createElement("span");
      status.className = "hold-label";
      status.textContent = " · Hold";
      meta.append(status);
    }
  }
  const scale = Number(zoom.value);
  const { canvas } = pane;
  const backdrop = byId("background").value;
  canvas.parentElement.dataset.bg = backdrop;
  const key = [clip.sheet, index, scale, guide.checked, backdrop].join("/");
  if (key === pane.lastDraw) return;
  pane.lastDraw = key;

  if (canvas.width !== width * scale) {
    canvas.width = width * scale;
    canvas.height = height * scale;
    // Keep the origin centered when a narrow stage must scroll at 4×.
    canvas.parentElement.scrollLeft = (canvas.width - canvas.parentElement.clientWidth) / 2;
  }

  const ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (guide.checked) {
    ctx.strokeStyle = backdrop === "dark" ? "#89b8ab" : "#334f4b";
    ctx.setLineDash([3 * scale, 3 * scale]);
    ctx.beginPath();
    ctx.moveTo(7 * scale, anchor.y * scale + .5);
    ctx.lineTo((width - 7) * scale, anchor.y * scale + .5);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = ctx.strokeStyle;
    ctx.fillRect(anchor.x * scale, (anchor.y + 1) * scale, scale, 3 * scale);
  }
  const [x, y, w, h] = clip.frames[index].rect;
  ctx.drawImage(images[clip.sheet], x, y, w, h, 0, 0, canvas.width, canvas.height);
  canvas.setAttribute("aria-label", "Lark, " + clip.label);
}

function render() {
  if (!ready) return;
  const current = frameAt(first(), time);
  draw(panes[0], first(), current);
  if (compare.checked) draw(panes[1], second(), frameAt(second(), time));
  seek.max = duration();
  seek.value = Math.floor(time);
  seek.setAttribute("aria-valuetext", seconds(time) + ", frame " + (current + 1));
  byId("clock").textContent = seconds(time);
  byId("length").textContent = seconds(duration()) + " TOTAL";
  byId("frame").textContent = "FRAME " + String(current + 1).padStart(2, "0") + " / " + String(first().frames.length).padStart(2, "0");
  byId("primary-name").textContent = first().label;
  play.textContent = playing ? "Pause" : "Play";
  play.setAttribute("aria-label", play.textContent);
}

function tick(timestamp) {
  request = null;
  if (lastTimestamp !== null) time += (timestamp - lastTimestamp) * Number(speed.value);
  lastTimestamp = timestamp;
  const end = duration();
  if (time >= end) {
    if (loop.checked) {
      time %= end;
    } else {
      time = end;
      setPlaying(false);
    }
  }
  render();
  schedule();
}

function schedule() {
  if (ready && playing && request === null && !document.hidden) request = requestAnimationFrame(tick);
}

function setPlaying(value) {
  if (value && time >= duration()) time = 0;
  playing = value;
  lastTimestamp = null;
  if (!value && request !== null) {
    cancelAnimationFrame(request);
    request = null;
  }
  render();
  schedule();
}

function step(direction) {
  // In comparison, advance through the union of both clips' pose changes.
  const starts = compare.checked
    ? [...new Set([...first().starts, ...second().starts])].sort((a, b) => a - b)
    : first().starts;
  const index = starts.findLastIndex(start => start <= time);
  const target = index + direction;
  const bounded = loop.checked
    ? (target + starts.length) % starts.length
    : Math.max(0, Math.min(starts.length - 1, target));
  time = starts[bounded];
  setPlaying(false);
}

for (const button of actions) {
  button.addEventListener("click", () => {
    active = button.dataset.action;
    for (const option of actions) option.setAttribute("aria-pressed", option === button);
    if (!compare.checked) loop.checked = first().loop;
    time = 0;
    lastTimestamp = null;
    render();
  });
}

play.addEventListener("click", () => setPlaying(!playing));
byId("prev").addEventListener("click", () => step(-1));
byId("next").addEventListener("click", () => step(1));
seek.addEventListener("input", () => {
  time = Number(seek.value);
  setPlaying(false);
});

compare.addEventListener("change", () => {
  byId("secondary-pane").hidden = !compare.checked;
  byId("sync-note").hidden = !compare.checked;
  byId("panes").classList.toggle("comparing", compare.checked);
  if (!compare.checked) loop.checked = first().loop;
  time = Math.min(time, duration());
  // The secondary canvas may have been laid out at a different width.
  panes[1].lastDraw = null;
  render();
});
comparison.addEventListener("change", () => {
  time = Math.min(time, duration());
  render();
});
for (const control of [zoom, byId("background"), guide]) control.addEventListener("change", render);
speed.addEventListener("change", () => { lastTimestamp = null; });
document.addEventListener("visibilitychange", () => {
  lastTimestamp = null;
  if (document.hidden && request !== null) {
    cancelAnimationFrame(request);
    request = null;
  }
  schedule();
});
reducedMotion.addEventListener("change", event => {
  if (event.matches) setPlaying(false);
});
document.addEventListener("keydown", event => {
  if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey ||
      event.target.closest("select, textarea, input:not([type=range]):not([type=checkbox]), [contenteditable]")) return;
  if (event.code === "Space") {
    if (event.target.closest("input, button")) return;
    event.preventDefault();
    if (!event.repeat) setPlaying(!playing);
  } else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    const stage = event.target.closest(".stage");
    if (stage && stage.scrollWidth > stage.clientWidth) return;
    event.preventDefault();
    step(event.key === "ArrowLeft" ? -1 : 1);
  }
});

Promise.all(Object.entries(sheets).map(async ([path, data]) => {
  const image = new Image();
  image.src = data;
  await image.decode();
  images[path] = image;
})).then(() => {
  ready = true;
  render();
  schedule();
}).catch(error => {
  console.error(error);
  byId("error").hidden = false;
});
