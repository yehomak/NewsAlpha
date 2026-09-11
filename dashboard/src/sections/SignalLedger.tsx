import { useEffect, useRef } from "react";
import type { Signal } from "../api";

interface Props {
  signals: Signal[] | null;
}

// ─── Sector colour lookup (subset of universe.py) ──────────────────────────
const SECTOR: Record<string, string> = {
  AAPL:"bigtech",MSFT:"bigtech",NVDA:"ai",GOOGL:"bigtech",META:"bigtech",
  CRM:"saas",NOW:"saas",WDAY:"saas",SNOW:"saas",DDOG:"saas",
  AMD:"ai",QCOM:"ai",AVGO:"ai",MRVL:"ai",INTC:"ai",
  CRWD:"cyber",PANW:"cyber",ZS:"cyber",
  COIN:"crypto",PYPL:"fintech",SHOP:"fintech",UBER:"fintech",
  AMZN:"bigtech",NFLX:"media",
  TSLA:"ev",GM:"auto",F:"auto",
  JPM:"finance",BAC:"finance",GS:"finance",MS:"finance",WFC:"finance",
  LLY:"health",ABBV:"health",MRK:"health",PFE:"health",
  AMGN:"health",GILD:"health",REGN:"health",
};

const SECTOR_COLOR: Record<string, string> = {
  ai:      "#3b82f6",
  bigtech: "#8b5cf6",
  finance: "#f59e0b",
  ev:      "#06b6d4",
  media:   "#10b981",
  saas:    "#a78bfa",
  crypto:  "#f97316",
  cyber:   "#ec4899",
  fintech: "#14b8a6",
  health:  "#84cc16",
  auto:    "#94a3b8",
};

const GROUP_ORDER = ["earnings", "product", "macro", "regulatory", "executive", "general"];
const GROUP_TINT: Record<string, string> = {
  earnings:   "rgba(34,197,94,0.025)",
  product:    "rgba(59,130,246,0.025)",
  macro:      "rgba(148,163,184,0.018)",
  regulatory: "rgba(239,68,68,0.025)",
  executive:  "rgba(139,92,246,0.025)",
  general:    "rgba(148,163,184,0.015)",
};

const DIR_COLOR: Record<string, string> = {
  bullish: "#22c55e",
  bearish: "#ef4444",
  neutral: "#3d5572",
};

// ─── Palette ───────────────────────────────────────────────────────────────
const C = {
  bg:      "#060a10",
  grid:    "#0b1520",
  rowHov:  "#0c1826",
  divider: "#0d1c2c",
  dim:     "#1a2d40",
  mid:     "#2d4558",
  text:    "#4a6880",
  hi:      "#7898b0",
  active:  "#a8c0d0",
};

// ─── Derive matrix structure from live signals ──────────────────────────────
interface LedgerEvent {
  id: number;
  title: string;
  type: string;
}
interface LedgerGroup {
  type: string;
  label: string;
  events: LedgerEvent[];
}
interface TickerStats {
  count: number; bull: number; bear: number; neut: number;
  evaled: number; correct: number; accuracy: number | null;
}

function deriveMatrix(signals: Signal[]) {
  // Unique tickers sorted by signal count
  const tcounts: Record<string, number> = {};
  for (const s of signals) tcounts[s.ticker] = (tcounts[s.ticker] ?? 0) + 1;
  const tickers = Object.keys(tcounts).sort((a, b) => tcounts[b] - tcounts[a]);

  // Unique events (deduped by event_id)
  const eventById: Record<number, LedgerEvent> = {};
  for (const s of signals) {
    if (!eventById[s.event_id]) {
      eventById[s.event_id] = {
        id:    s.event_id,
        title: s.event_title ?? `Event #${s.event_id}`,
        type:  s.event_type,
      };
    }
  }

  // Group events by type
  const groups: LedgerGroup[] = GROUP_ORDER
    .map(type => ({
      type,
      label: type.toUpperCase(),
      events: Object.values(eventById).filter(e => e.type === type),
    }))
    .filter(g => g.events.length > 0);

  // Cell lookup: `${event_id}_${ticker}` → signal
  const cellMap: Record<string, Signal> = {};
  for (const s of signals) cellMap[`${s.event_id}_${s.ticker}`] = s;

  // Per-ticker stats
  const tStats: Record<string, TickerStats> = {};
  for (const t of tickers) {
    const sigs   = signals.filter(s => s.ticker === t);
    const evaled = sigs.filter(s => s.correct !== null);
    const corr   = evaled.filter(s => s.correct === true).length;
    tStats[t] = {
      count:    sigs.length,
      bull:     sigs.filter(s => s.direction === "bullish").length,
      bear:     sigs.filter(s => s.direction === "bearish").length,
      neut:     sigs.filter(s => s.direction === "neutral").length,
      evaled:   evaled.length,
      correct:  corr,
      accuracy: evaled.length > 0 ? corr / evaled.length : null,
    };
  }

  return { tickers, groups, cellMap, tStats };
}

// ─── Component ─────────────────────────────────────────────────────────────
export function SignalLedger({ signals }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tipRef    = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const tip    = tipRef.current;
    if (!canvas || !tip) return;

    if (!signals || signals.length === 0) {
      const ctx = canvas.getContext("2d")!;
      const dpr = window.devicePixelRatio || 1;
      canvas.width  = window.innerWidth  * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width  = window.innerWidth  + "px";
      canvas.style.height = window.innerHeight + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);
      ctx.fillStyle = C.mid;
      ctx.font = "11px ui-monospace, monospace";
      ctx.textAlign = "center";
      ctx.fillText(
        signals === null ? "loading signals…" : "no signals yet",
        window.innerWidth / 2,
        window.innerHeight / 2,
      );
      return;
    }

    const { tickers, groups, cellMap, tStats } = deriveMatrix(signals);

    // Build flat row list
    const rows: ({ isHeader: true; group: LedgerGroup } | { isHeader: false; event: LedgerEvent })[] = [];
    for (const g of groups) {
      rows.push({ isHeader: true, group: g });
      for (const e of g.events) rows.push({ isHeader: false, event: e });
    }

    // Layout constants
    const LM   = 224;
    const RM   = 12;
    const TM   = 64;
    const BOTT = 168;
    const GH   = 20;
    const RH   = 22;
    const NTICKERS = tickers.length;

    let W: number, H: number, DIV_Y: number, gridW: number, COL_W: number;

    const ctx = canvas.getContext("2d")!;

    function layout() {
      const dpr = window.devicePixelRatio || 1;
      W = window.innerWidth;
      H = window.innerHeight;
      canvas.width        = W * dpr;
      canvas.height       = H * dpr;
      canvas.style.width  = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      DIV_Y = H - BOTT;
      gridW = W - LM - RM;
      COL_W = NTICKERS > 0 ? gridW / NTICKERS : 1;
    }

    // Mutable hover + scroll state (not React state — avoids re-render)
    let hovRow: number | null  = null;   // event id
    let hovCol: string | null  = null;   // ticker id
    let scrollY                = 0;
    const MATRIX_H = groups.length * GH + (rows.length - groups.length) * RH;

    function trunc(s: string, n: number) {
      return s.length > n ? s.slice(0, n - 1) + "…" : s;
    }
    function fmtAcc(acc: number | null) {
      return acc !== null ? Math.round(acc * 100) + "%" : "—";
    }

    // ── Draw ──────────────────────────────────────────────────────────────
    function draw() {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, W, H);

      // ── Ticker header ────────────────────────────────────────────────────
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, W, TM);
      ctx.fillStyle = C.divider;
      ctx.fillRect(LM, TM - 1, gridW, 1);

      for (let ci = 0; ci < NTICKERS; ci++) {
        const t  = tickers[ci];
        const st = tStats[t];
        const cx = LM + ci * COL_W + COL_W / 2;
        const isH = hovCol === t;

        // Column hover shade in matrix
        if (isH) {
          ctx.fillStyle = C.rowHov;
          ctx.fillRect(LM + ci * COL_W, TM, COL_W, DIV_Y - TM);
        }

        // Sector bar
        const sc = SECTOR_COLOR[SECTOR[t] ?? ""] ?? C.mid;
        ctx.fillStyle = isH ? sc : sc + "80";
        ctx.fillRect(LM + ci * COL_W + 2, 0, COL_W - 4, 3);

        // Ticker label
        ctx.font      = `${isH ? 700 : 600} ${isH ? 12 : 11}px ui-monospace, monospace`;
        ctx.fillStyle = isH ? C.active : C.text;
        ctx.textAlign = "center";
        ctx.textBaseline = "alphabetic";
        ctx.fillText(t, cx, 22);

        // Count · accuracy
        ctx.font      = "9px ui-monospace, monospace";
        ctx.fillStyle = isH ? C.hi : C.mid;
        ctx.fillText(`${st.count} · ${fmtAcc(st.accuracy)}`, cx, 36);

        // Bull/neut/bear micro bars
        const baseIx = cx - 9;
        const dirs = [
          { n: st.bull, c: DIR_COLOR.bullish },
          { n: st.neut, c: DIR_COLOR.neutral },
          { n: st.bear, c: DIR_COLOR.bearish },
        ];
        let ix = baseIx;
        for (const d of dirs) {
          ctx.fillStyle = d.n > 0 ? d.c : C.dim;
          ctx.globalAlpha = d.n > 0 ? (isH ? 1 : 0.7) : 0.3;
          ctx.fillRect(ix, 48, 5, 3);
          ctx.globalAlpha = 1;
          ix += 8;
        }
      }

      // Left axis label
      ctx.font      = "9px ui-monospace, monospace";
      ctx.fillStyle = C.mid;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText("EVENT", LM - 10, TM / 2);

      // ── Clipped scrollable matrix ─────────────────────────────────────────
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, TM, W, DIV_Y - TM);
      ctx.clip();
      ctx.translate(0, TM - scrollY);

      let y = 0;
      for (const row of rows) {
        if (row.isHeader) {
          const g = row.group;
          ctx.fillStyle = GROUP_TINT[g.type] ?? "transparent";
          ctx.fillRect(0, y, W, GH);
          ctx.font      = "8px ui-monospace, monospace";
          ctx.fillStyle = C.mid;
          ctx.textAlign = "left";
          ctx.textBaseline = "middle";
          ctx.fillText(g.label, 8, y + GH / 2);
          ctx.fillStyle = C.divider;
          ctx.fillRect(LM, y + GH - 1, gridW, 1);
          y += GH;
        } else {
          const ev  = row.event;
          const isR = hovRow === ev.id;

          if (isR) {
            ctx.fillStyle = C.rowHov;
            ctx.fillRect(LM, y, gridW, RH);
          }
          ctx.fillStyle = C.grid;
          ctx.fillRect(LM, y + RH - 1, gridW, 1);

          // Event label
          ctx.font      = `${isR ? 500 : 400} 10px ui-monospace, monospace`;
          ctx.fillStyle = isR ? C.hi : C.text;
          ctx.textAlign = "right";
          ctx.textBaseline = "middle";
          ctx.fillText(trunc(ev.title, 36), LM - 8, y + RH / 2);

          // Cells
          for (let ci = 0; ci < NTICKERS; ci++) {
            const t   = tickers[ci];
            const sig = cellMap[`${ev.id}_${t}`];
            const cx  = LM + ci * COL_W + COL_W / 2;
            const cy  = y + RH / 2;

            ctx.fillStyle = C.grid;
            ctx.fillRect(LM + ci * COL_W, y, 1, RH);

            if (!sig) {
              ctx.beginPath();
              ctx.arc(cx, cy, 1, 0, Math.PI * 2);
              ctx.fillStyle = C.dim;
              ctx.globalAlpha = 0.3;
              ctx.fill();
              ctx.globalAlpha = 1;
            } else {
              const r     = 2.5 + sig.confidence * 6.5;
              const color = DIR_COLOR[sig.direction] ?? C.mid;
              const anyH  = hovRow !== null || hovCol !== null;
              const rel   = isR || hovCol === t;
              ctx.globalAlpha = anyH ? (rel ? 1 : 0.1) : 0.82;

              ctx.beginPath();
              ctx.arc(cx, cy, r, 0, Math.PI * 2);
              ctx.fillStyle = color + (isR && hovCol === t ? "ff" : "cc");
              ctx.fill();

              if (sig.correct !== null) {
                ctx.fillStyle = `rgba(255,255,255,${sig.correct ? 0.9 : 0.55})`;
                ctx.font = `${Math.max(6, Math.round(r * 1.1))}px ui-monospace, monospace`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(sig.correct ? "✓" : "✗", cx, cy + 0.5);
              } else {
                ctx.beginPath();
                ctx.arc(cx, cy, Math.max(1, r * 0.2), 0, Math.PI * 2);
                ctx.fillStyle = "rgba(255,255,255,0.35)";
                ctx.fill();
              }
              ctx.globalAlpha = 1;
            }
          }
          ctx.fillStyle = C.grid;
          ctx.fillRect(LM + NTICKERS * COL_W, y, 1, RH);
          y += RH;
        }
      }

      ctx.restore();

      // ── Divider ───────────────────────────────────────────────────────────
      ctx.fillStyle = C.divider;
      ctx.fillRect(0, DIV_Y, W, 2);

      // ── Bottom bar chart ──────────────────────────────────────────────────
      const BP_TOP    = DIV_Y + 2;
      const BAR_TOP   = BP_TOP + 18;
      const MAX_BAR_H = BOTT - 68;
      const maxSigs   = Math.max(...tickers.map(t => tStats[t].count), 1);

      ctx.font      = "8px ui-monospace, monospace";
      ctx.fillStyle = C.mid;
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.fillText("SIGNAL DISTRIBUTION  ·  sorted by coverage", LM, BP_TOP + 13);

      for (let ci = 0; ci < NTICKERS; ci++) {
        const t  = tickers[ci];
        const st = tStats[t];
        const bx = LM + ci * COL_W + 4;
        const bw = COL_W - 8;
        const isH = hovCol === t;
        const cx = LM + ci * COL_W + COL_W / 2;
        const base = BAR_TOP + MAX_BAR_H;

        ctx.globalAlpha = isH ? 1 : 0.7;

        const bearH = (st.bear / maxSigs) * MAX_BAR_H;
        const neutH = (st.neut / maxSigs) * MAX_BAR_H;
        const bullH = (st.bull / maxSigs) * MAX_BAR_H;
        let sy = base;
        if (st.bear > 0) { sy -= bearH; ctx.fillStyle = DIR_COLOR.bearish + (isH ? "ff" : "aa"); ctx.fillRect(bx, sy, bw, bearH); }
        if (st.neut > 0) { sy -= neutH; ctx.fillStyle = DIR_COLOR.neutral + (isH ? "ff" : "99"); ctx.fillRect(bx, sy, bw, neutH); }
        if (st.bull > 0) { sy -= bullH; ctx.fillStyle = DIR_COLOR.bullish + (isH ? "ff" : "aa"); ctx.fillRect(bx, sy, bw, bullH); }

        const barH = (st.count / maxSigs) * MAX_BAR_H;
        if (st.count > 0) {
          ctx.font      = "9px ui-monospace, monospace";
          ctx.fillStyle = isH ? C.active : C.text;
          ctx.textAlign = "center";
          ctx.textBaseline = "alphabetic";
          ctx.fillText(String(st.count), cx, base - barH - 3);
        }

        ctx.globalAlpha = 1;

        // Accuracy label
        const acc = st.accuracy;
        const accColor = acc !== null
          ? (acc >= 0.60 ? DIR_COLOR.bullish : acc >= 0.48 ? "#f59e0b" : DIR_COLOR.bearish)
          : C.dim;
        ctx.font      = "8px ui-monospace, monospace";
        ctx.fillStyle = isH ? accColor : accColor + "99";
        ctx.textAlign = "center";
        ctx.textBaseline = "alphabetic";
        ctx.fillText(fmtAcc(acc), cx, base + 11);

        // Ticker label
        const sc = SECTOR_COLOR[SECTOR[t] ?? ""] ?? C.mid;
        ctx.font      = `${isH ? 600 : 500} ${isH ? 11 : 10}px ui-monospace, monospace`;
        ctx.fillStyle = isH ? C.active : C.text;
        ctx.textAlign = "center";
        ctx.fillText(t, cx, base + 24);

        // Sector dot
        ctx.beginPath();
        ctx.arc(cx, base + 33, 2, 0, Math.PI * 2);
        ctx.fillStyle = isH ? sc : sc + "70";
        ctx.fill();
      }

      // Bottom stat line
      const evCount = Object.keys(
        signals.reduce<Record<number, true>>((m, s) => { m[s.event_id] = true; return m; }, {})
      ).length;
      const density = NTICKERS > 0 && evCount > 0
        ? Math.round((signals.length / (evCount * NTICKERS)) * 100)
        : 0;
      ctx.font      = "9px ui-monospace, monospace";
      ctx.fillStyle = C.mid;
      ctx.textAlign = "left";
      ctx.fillText(
        `${signals.length} signals · ${NTICKERS} tickers · ${evCount} events · ${density}% matrix density`,
        LM, H - 10,
      );
      ctx.fillStyle = C.dim;
      ctx.fillText("butterfly-effect · signal ledger", 8, H - 10);
    }

    // ── Interaction ────────────────────────────────────────────────────────
    function rowAtY(sy: number): number | null {
      const cy = sy - TM + scrollY;
      if (cy < 0) return null;
      let y = 0;
      for (const row of rows) {
        const h = row.isHeader ? GH : RH;
        if (cy >= y && cy < y + h) return row.isHeader ? null : (row as { isHeader: false; event: LedgerEvent }).event.id;
        y += h;
      }
      return null;
    }

    function colAtX(sx: number): string | null {
      if (sx < LM || sx > W - RM) return null;
      const ci = Math.floor((sx - LM) / COL_W);
      return ci >= 0 && ci < NTICKERS ? tickers[ci] : null;
    }

    function onMouseMove(ev: MouseEvent) {
      const inMatrix = ev.clientY >= TM && ev.clientY < DIV_Y;
      hovRow = inMatrix ? rowAtY(ev.clientY) : null;
      hovCol = colAtX(ev.clientX);

      const sig = hovRow !== null && hovCol !== null ? cellMap[`${hovRow}_${hovCol}`] : null;
      let html = "";

      if (sig) {
        const evObj = rows.find(r => !r.isHeader && (r as { isHeader: false; event: LedgerEvent }).event.id === hovRow);
        const evTitle = evObj && !evObj.isHeader ? (evObj as { isHeader: false; event: LedgerEvent }).event.title : "";
        const evalStr = sig.correct === null
          ? `<span style="color:${C.mid}">pending</span>`
          : sig.correct
          ? `<span style="color:${DIR_COLOR.bullish}">✓ correct</span>`
          : `<span style="color:${DIR_COLOR.bearish}">✗ incorrect</span>`;
        html = `<div style="font-size:14px;font-weight:700;color:#c8dde8;margin-bottom:3px">${hovCol} <span style="color:${DIR_COLOR[sig.direction] ?? C.mid};font-weight:400;font-size:11px">${sig.direction === "bullish" ? "↑" : sig.direction === "bearish" ? "↓" : "–"}</span></div>
          <div style="color:${C.mid};font-size:10px;margin-bottom:6px">${sig.event_type}</div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span>confidence</span><span style="color:${C.hi}">${Math.round(sig.confidence * 100)}%</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span>eval</span><span>${evalStr}</span></div>
          <hr style="border:none;border-top:1px solid #0f1e2c;margin:5px 0">
          <div style="color:${C.hi};font-size:10px;line-height:1.4">${evTitle}</div>`;
      } else if (hovCol) {
        const st  = tStats[hovCol];
        const acc = fmtAcc(st.accuracy);
        html = `<div style="font-size:14px;font-weight:700;color:#c8dde8;margin-bottom:3px">${hovCol}</div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span>signals</span><span style="color:${C.hi}">${st.count}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span>↑ bullish</span><span style="color:${DIR_COLOR.bullish}">${st.bull}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span>↓ bearish</span><span style="color:${DIR_COLOR.bearish}">${st.bear}</span></div>
          <div style="display:flex;justify-content:space-between;gap:16px"><span>accuracy</span><span style="color:${C.hi}">${st.evaled > 0 ? Math.round(st.accuracy! * 100) + "% (" + st.correct + "/" + st.evaled + ")" : "pending"}</span></div>`;
      } else if (hovRow !== null) {
        const evObj = rows.find(r => !r.isHeader && (r as { isHeader: false; event: LedgerEvent }).event.id === hovRow);
        if (evObj && !evObj.isHeader) {
          const ev  = (evObj as { isHeader: false; event: LedgerEvent }).event;
          const sigs = signals.filter(s => s.event_id === hovRow);
          const tgts = sigs.map(s => `<span style="color:${DIR_COLOR[s.direction] ?? C.mid}">${s.ticker}</span>`).join(" · ");
          html = `<div style="font-size:12px;font-weight:600;color:#8aafc8;line-height:1.4;margin-bottom:4px">${ev.title}</div>
            <div style="color:${C.mid};font-size:10px;margin-bottom:6px">${ev.type}</div>
            <div style="display:flex;justify-content:space-between;gap:16px"><span>signals</span><span style="color:${C.hi}">${sigs.length}</span></div>
            <hr style="border:none;border-top:1px solid #0f1e2c;margin:5px 0">
            <div style="color:${C.mid};font-size:10px">${tgts}</div>`;
        }
      }

      if (html) {
        tip.innerHTML = html;
        tip.style.display = "block";
        const tx = Math.min(ev.clientX + 16, window.innerWidth - 270);
        const ty = Math.min(ev.clientY + 12, window.innerHeight - 170);
        tip.style.left = tx + "px";
        tip.style.top  = ty + "px";
      } else {
        tip.style.display = "none";
      }

      draw();
    }

    function onMouseLeave() {
      hovRow = null; hovCol = null;
      tip.style.display = "none";
      draw();
    }

    function onWheel(ev: WheelEvent) {
      if (ev.clientY < TM || ev.clientY > DIV_Y) return;
      ev.preventDefault();
      const maxScroll = Math.max(0, MATRIX_H - (DIV_Y - TM));
      scrollY = Math.max(0, Math.min(maxScroll, scrollY + ev.deltaY * 0.6));
      draw();
    }

    function onResize() { layout(); draw(); }

    layout();
    draw();

    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseleave", onMouseLeave);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("resize", onResize);

    return () => {
      canvas.removeEventListener("mousemove", onMouseMove);
      canvas.removeEventListener("mouseleave", onMouseLeave);
      canvas.removeEventListener("wheel", onWheel);
      window.removeEventListener("resize", onResize);
    };
  }, [signals]);

  return (
    <div style={{ position: "relative", width: "100vw", height: "100vh", overflow: "hidden" }}>
      <canvas ref={canvasRef} style={{ display: "block" }} />
      <div
        ref={tipRef}
        style={{
          position: "fixed", pointerEvents: "none", display: "none", zIndex: 20,
          background: "rgba(4,7,12,0.97)", border: "1px solid #142030",
          borderRadius: 4, padding: "9px 13px", fontSize: 10.5,
          fontFamily: "'SF Mono','Cascadia Code',ui-monospace,monospace",
          lineHeight: 1.65, maxWidth: 260, color: "#4a6880",
          boxShadow: "0 4px 16px rgba(0,0,0,0.7)",
        }}
      />
    </div>
  );
}
