const $ = (sel) => document.querySelector(sel);

const estado = {
  slots: {},
  slot: null,
  effort: "medium",
  cache: false,
  json: false,
  turnos: 0,
  gasto: 0,
};


async function arrancar() {
  const r = await fetch("/api/modelos");
  estado.slots = (await r.json()).slots;

  const cont = $("#modelos");
  cont.innerHTML = "";
  for (const [n, cfg] of Object.entries(estado.slots)) {
    const b = document.createElement("button");
    b.className = "modelo";
    b.dataset.slot = n;
    b.innerHTML = `
      <div class="nombre">${cfg.alias}<span class="slot">slot ${n}</span></div>
      <div class="prov">${cfg.proveedor}</div>
      <div class="cap">${cfg.capacidad}</div>
      <div class="precio">$${cfg.precio_in} in / $${cfg.precio_out} out por millon</div>`;
    b.onclick = () => elegirModelo(n);
    cont.appendChild(b);
  }
  elegirModelo("1");
}

async function elegirModelo(n) {
  estado.slot = n;
  estado.turnos = 0;
  estado.gasto = 0;
  // Cada capacidad pertenece a su slot. Sin esto, los interruptores quedarian activos al
  // cambiar de modelo y le aplicarian a un slot una capacidad que no es la suya.
  estado.cache = estado.slots[n].control === "cache";
  estado.json = estado.slots[n].control === "json";
  document.querySelectorAll(".modelo").forEach((b) =>
    b.classList.toggle("activo", b.dataset.slot === n)
  );

  const r = await fetch("/api/conversacion", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slot: n }),
  });
  const d = await r.json();

  $("#chat").innerHTML = "";
  $("#log").textContent = d.log;
  actualizarTotales();
  dibujarControles();
  agregarAviso(`Conversacion nueva con ${estado.slots[n].alias}.`);
}

function dibujarControles() {
  const cfg = estado.slots[estado.slot];
  const cont = $("#controles");
  cont.innerHTML = "<h2>Parametros</h2>";

  if (cfg.razona) {
    const g = document.createElement("div");
    g.className = "grupo";
    g.innerHTML = `<label>reasoning.effort</label><div class="segmentado"></div>`;
    const seg = g.querySelector(".segmentado");
    ["low", "medium", "high"].forEach((nivel) => {
      const b = document.createElement("button");
      b.textContent = nivel;
      b.className = nivel === estado.effort ? "activo" : "";
      b.onclick = () => {
        estado.effort = nivel;
        dibujarControles();
      };
      seg.appendChild(b);
    });
    cont.appendChild(g);
  }

  if (cfg.control === "cache") {
    cont.appendChild(interruptor("cache_control ephemeral", "cache",
      "Antepone el bloque estatico de contexto/ para provocar cache hits."));
  }
  if (cfg.control === "json") {
    cont.appendChild(interruptor("response_format JSON Schema", "json",
      "Exige la respuesta contra el esquema definido en app.py."));
  }
}

function interruptor(texto, clave, ayuda) {
  const g = document.createElement("div");
  g.className = "grupo";
  const l = document.createElement("label");
  l.className = "interruptor";
  const i = document.createElement("input");
  i.type = "checkbox";
  i.checked = estado[clave];
  i.onchange = () => (estado[clave] = i.checked);
  l.append(i, document.createTextNode(texto));
  g.appendChild(l);
  const p = document.createElement("p");
  p.className = "aviso";
  p.textContent = ayuda;
  g.appendChild(p);
  return g;
}


function escapar(t) {
  return t.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

/** Render minimo: separa los bloques cercados en ``` y les pone boton de copiar. */
function cuerpo(texto) {
  const div = document.createElement("div");
  div.className = "burbuja";
  texto.split(/```/).forEach((trozo, i) => {
    if (i % 2 === 0) {
      div.appendChild(document.createTextNode(trozo));
      return;
    }
    const codigo = trozo.replace(/^[a-zA-Z0-9]*\n/, "");
    const pre = document.createElement("pre");
    pre.innerHTML = `<code>${escapar(codigo)}</code>`;
    const b = document.createElement("button");
    b.className = "copiar";
    b.textContent = "Copiar";
    b.onclick = () => {
      navigator.clipboard.writeText(codigo);
      b.textContent = "Copiado";
      setTimeout(() => (b.textContent = "Copiar"), 1200);
    };
    div.append(pre, b);
  });
  return div;
}

function agregarMensaje(rol, texto) {
  const m = document.createElement("div");
  m.className = `mensaje ${rol}`;
  const r = document.createElement("div");
  r.className = "rol";
  r.textContent = rol;
  m.append(r, cuerpo(texto));
  $("#chat").appendChild(m);
  m.scrollIntoView({ block: "end" });
  return m;
}

function agregarAviso(texto) {
  const p = document.createElement("div");
  p.className = "rol";
  p.textContent = texto;
  $("#chat").appendChild(p);
}

function agregarUsage(m, u) {
  const d = document.createElement("div");
  d.className = "usage";
  const pills = [
    ["entrada", u.entrada, ""],
    ["cacheados", u.cacheados, u.cacheados > 0 ? "hit" : ""],
    ["escritos en cache", u.escritos_cache, ""],
    ["salida", u.salida, ""],
    ["razonamiento", u.razonamiento, ""],
    ["costo", "$" + u.costo.toFixed(6), "costo"],
    ["descuento cache", "$" + u.descuento_cache.toFixed(6), ""],
  ];
  pills.forEach(([k, v, cls]) => {
    const s = document.createElement("span");
    s.className = cls;
    s.innerHTML = `${k} <b>${v}</b>`;
    d.appendChild(s);
  });
  m.appendChild(d);
}

function actualizarTotales() {
  $("#turnos").textContent = estado.turnos;
  $("#gasto").textContent = "$" + estado.gasto.toFixed(6);
}


async function mandar(texto) {
  agregarMensaje("user", texto);
  const espera = agregarMensaje("assistant", "pensando...");
  espera.querySelector(".burbuja").classList.add("pensando");
  $("#mandar").disabled = true;

  try {
    const r = await fetch("/api/mensaje", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        texto,
        effort: estado.effort,
        cache: estado.cache,
        json: estado.json,
      }),
    });
    const d = await r.json();
    espera.remove();

    if (!r.ok) {
      const m = agregarMensaje("assistant", d.error || "Error desconocido");
      m.querySelector(".burbuja").classList.add("error");
      return;
    }

    const m = agregarMensaje("assistant", d.respuesta);
    agregarUsage(m, d.usage);
    estado.turnos = d.turno;
    estado.gasto = d.acumulado;
    $("#log").textContent = d.log;
    actualizarTotales();
  } catch (e) {
    espera.remove();
    const m = agregarMensaje("assistant", String(e));
    m.querySelector(".burbuja").classList.add("error");
  } finally {
    $("#mandar").disabled = false;
  }
}

$("#compositor").onsubmit = (e) => {
  e.preventDefault();
  const t = $("#texto").value.trim();
  if (!t) return;
  $("#texto").value = "";
  mandar(t);
};

$("#texto").onkeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#compositor").requestSubmit();
  }
};

$("#archivo").onchange = async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  $("#texto").value = await f.text();
  e.target.value = "";
  $("#texto").focus();
};

arrancar();
