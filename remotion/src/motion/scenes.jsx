// Scene catalog. Each scene is full-frame 1080x1920, timed in local frames, and places its own sounds.
// Every scene keeps important content inside the safe zone: y 220..1470, x 60..1020 (formats.md).
// Catalog and when to use each one: the reels skill/formats.md. All text comes from props (the reel plan).
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {W, H, clamp, easeOut, easeInOut, usePop, popAt, useIn, blurFor, useBrand, Sfx, Icon, IconBadge, Words, Chip, Camera, Photo} from './kit';

const Stack = ({top = 300, children, gap = 34, align = 'center'}) => (
  <div style={{position: 'absolute', left: 60, right: 60, top, display: 'flex', flexDirection: 'column', alignItems: align === 'center' ? 'center' : 'flex-start', gap}}>{children}</div>
);

// ---- Backdrop: black, brand pattern drifting upward (the "scrolling background"), blue glow -------------
export const Backdrop = ({pattern, speed = 0.6, glow = true, hide = []}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const y = -(frame * speed) % 600;
  // strict (organic): no glow, and no pattern behind product images or photos (guide p65, p107)
  if (b.strict) glow = false;
  if (b.strict && hide.some(([a, z]) => frame >= a && frame < z)) pattern = null;
  return (
    <AbsoluteFill style={{background: b.ink}}>
      {pattern ? (
        <div style={{position: 'absolute', left: -60, right: -60, top: y - 60, height: H + 1400, opacity: 0.22,
          backgroundImage: `url(${staticFile(pattern)})`, backgroundSize: '600px auto', backgroundRepeat: 'repeat'}} />
      ) : null}
      {glow ? <div style={{position: 'absolute', left: W * 0.5 - 700, top: H * 0.38 - 700, width: 1400, height: 1400, borderRadius: 700,
        background: 'radial-gradient(circle, rgba(255,59,47,0.20) 0%, rgba(255,59,47,0.0) 62%)'}} /> : null}
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 45%, rgba(0,0,0,0.7) 100%)'}} />
    </AbsoluteFill>
  );
};

// ---- IconSwarm: N icons pop into a grid, faster and faster, then the headline slams over them -------------
// props: icon, count, lines [{text, emph}], cols, label (small text under the count)
export const IconSwarm = ({icon = 'bolt', count = 16, cols = 4, lines = [], dur = 90, label}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const cell = Math.min(200, 940 / cols);
  const rows = Math.ceil(count / cols);
  const gx = W / 2 - (cols * cell) / 2;
  const gy = 520;
  // accelerating arrival: icon k lands at 30 * sqrt(k/count) frames
  const tk = (k) => Math.round(22 * Math.sqrt(k / count));
  const textAt = tk(count - 1) + 4;
  const dimGrid = interpolate(frame, [textAt, textAt + 6], [1, 0.32], clamp);
  return (
    <AbsoluteFill>
      <Camera dur={dur} push={0.06} shakeAt={textAt}>
        <div style={{position: 'absolute', left: gx, top: gy, width: cols * cell, height: rows * cell, opacity: dimGrid}}>
          {Array.from({length: count}).map((_, k) => {
            const local = frame - tk(k) + 3;
            const p = local < 0 ? 0 : Math.min(1.12, interpolate(local, [0, 4], [0, 1.12], clamp) - interpolate(local, [4, 8], [0, 0.12], clamp));
            return (
              <div key={k} style={{position: 'absolute', left: (k % cols) * cell, top: Math.floor(k / cols) * cell, width: cell, height: cell,
                display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${p})`}}>
                <IconBadge name={icon} size={cell * 0.8} />
              </div>
            );
          })}
        </div>
        <Stack top={560}>
          {lines.map((ln, i) => (
            <Words key={i} text={ln.text} emph={ln.emph || []} at={textAt + i * 12} size={ln.size || 132} stagger={2} pill={ln.pill} />
          ))}
          {label ? <div style={{marginTop: 10}}><Words text={label} at={textAt + lines.length * 12 + 4} size={44} weight={500} mode="rise" color={b.muted} /></div> : null}
        </Stack>
      </Camera>
      {Array.from({length: count}).filter((_, k) => count <= 16 || k % Math.ceil(count / 16) === 0).map((_, k) => <Sfx key={k} name="tick" at={tk(k * Math.max(1, Math.ceil(count / 16)))} volume={0.35} />)}
      <Sfx name="impact" at={textAt} volume={0.8} />
      {lines.slice(1).map((_, i) => <Sfx key={`p${i}`} name="pop" at={textAt + (i + 1) * 12} volume={0.5} />)}
    </AbsoluteFill>
  );
};

// ---- Kinetic: big words over a real photo (or the backdrop) ------------------------------------------
// props: lines [{text, emph, size, pill}], photo, kicker, icon, top
export const Kinetic = ({imagery = "generic", lines = [], photo, kicker, icon, hero, heroSize = 760, dur = 90, top = 420, gap = 16}) => {
  const b = useBrand();
  let at = 4;
  const starts = lines.map((ln) => {
    const s = at;
    at += Math.max(10, ln.text.split(' ').length * 3 + 8);
    return s;
  });
  return (
    <AbsoluteFill>
      {photo ? <Photo src={photo} imagery={imagery} dur={dur} dim={0.55} /> : null}
      <Camera dur={dur} push={0.04}>
        <Stack top={top} gap={gap}>
          {kicker ? <Chip text={kicker} at={0} size={36} /> : null}
          {icon ? <div style={{transform: `scale(${usePop(2)})`}}><IconBadge name={icon} size={170} /></div> : null}
          {hero ? <div style={{transform: `scale(${usePop(2)})`, marginBottom: 30}}><Icon name={hero} size={heroSize} style={{height: heroSize * 0.8, filter: 'drop-shadow(0 0 24px rgba(255,59,47,0.5))'}} /></div> : null}
          {lines.map((ln, i) => <Words key={i} text={ln.text} emph={ln.emph || []} at={starts[i]} size={ln.size || 112} pill={ln.pill} mode={ln.mode || 'slam'} weight={ln.weight || 900} />)}
        </Stack>
      </Camera>
      {kicker || icon ? <Sfx name="pop" at={2} volume={0.45} /> : null}
      {starts.map((s, i) => <Sfx key={i} name={i === 0 ? 'whoosh' : 'pop'} at={s + 2} volume={i === 0 ? 0.45 : 0.5} />)}
    </AbsoluteFill>
  );
};

// ---- IconList: rows of icon + label arrive one at a time; mark 'x' strikes them, 'check' ticks them --------
// props: title {text, emph}, rows [{icon, text}], mark: null|'x'|'check'
export const IconList = ({title, rows = [], mark = null, dur = 90, every = 11, top = 470}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const t0 = title ? 12 : 2;
  return (
    <AbsoluteFill>
      <Camera dur={dur} push={0.035}>
        <Stack top={top} gap={54} align="left">
          {title ? <Words text={title.text} emph={title.emph || []} at={0} size={title.size || 96} align="left" /> : null}
          {rows.map((r, i) => {
            const at = t0 + i * every;
            const p = interpolate(frame - at, [0, 8], [0, 1], {...clamp, easing: easeOut});
            const markAt = at + 6;
            const mp = usePop(markAt);
            const strike = mark === 'x' ? interpolate(frame - markAt, [0, 6], [0, 1], clamp) : 0;
            return (
              <div key={i} style={{display: 'flex', alignItems: 'center', gap: 34, opacity: p, transform: `translateX(${(1 - p) * -140}px)`, filter: blurFor(p, 10)}}>
                <div style={{position: 'relative'}}>
                  <IconBadge name={r.icon} size={160} />
                  {mark ? <div style={{position: 'absolute', right: -14, bottom: -14, transform: `scale(${mp})`}}>
                    <div style={{width: 64, height: 64, borderRadius: 32, background: mark === 'x' ? b.warn : b.ok, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                      <Icon name={mark === 'x' ? 'x' : 'check'} size={44} color="#000" />
                    </div></div> : null}
                </div>
                <div style={{position: 'relative', fontFamily: b.font, fontWeight: 800, fontSize: r.size || 74, color: b.white, lineHeight: 1.05, whiteSpace: 'nowrap'}}>
                  {r.text}
                  {mark === 'x' ? <div style={{position: 'absolute', left: 0, top: '52%', height: 8, width: `${strike * 100}%`, background: b.warn, borderRadius: 4}} /> : null}
                </div>
              </div>
            );
          })}
        </Stack>
      </Camera>
      {rows.map((_, i) => <Sfx key={i} name="whoosh" at={t0 + i * every + 2} volume={0.35} />)}
      {mark ? rows.map((_, i) => <Sfx key={`m${i}`} name={mark === 'x' ? 'click' : 'pop'} at={t0 + i * every + 6} volume={0.5} />) : null}
    </AbsoluteFill>
  );
};

// ---- Compare: two columns, rows count and bars shrink (before vs after) -------------------------------
// props: title, left {label, icon}, right {label, icon}, rows [{label, a, b, unit, prefix, bars: true}]
const fmt = (v, dec) => (dec ? v.toFixed(dec) : Math.round(v).toString());
export const Compare = ({title, left, right, rows = [], dur = 150, every = 26}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const colW = 440;
  const head = (c, x, tint, at) => {
    const p = usePop(at);
    return (
      <div style={{position: 'absolute', left: x, top: 500, width: colW, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18, transform: `scale(${p})`}}>
        <IconBadge name={c.icon} size={140} ring={tint} color={tint} />
        <div style={{fontFamily: b.font, fontWeight: 800, fontSize: 50, color: tint, textAlign: 'center', lineHeight: 1.05}}>{c.label}</div>
      </div>
    );
  };
  return (
    <AbsoluteFill>
      <Camera dur={dur} push={0.03}>
        <div style={{position: 'absolute', left: 60, right: 60, top: 300, display: 'flex', justifyContent: 'center'}}>
          {title ? <Words text={title.text} emph={title.emph || []} at={0} size={title.size || 80} /> : null}
        </div>
        {head(left, 70, b.muted, 6)}
        {head(right, W - 70 - colW, b.accent, 12)}
        <div style={{position: 'absolute', left: W / 2 - 2, top: 500, width: 4, height: 920, background: 'rgba(255,255,255,0.12)'}} />
        {rows.map((r, i) => {
          const at = 26 + i * every;
          const y = 900 + i * 300;
          const p = interpolate(frame - at, [0, 18], [0, 1], {...clamp, easing: easeOut});
          const lp = useIn(at - 4, 8);
          const maxV = Math.max(r.a, r.b);
          const cell = (v, x, tint, big) => (
            <div style={{position: 'absolute', left: x, top: y, width: colW, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
              <div style={{fontFamily: b.font, fontWeight: 900, fontSize: big ? 140 : 120, color: tint, lineHeight: 1}}>
                {r.prefix || ''}{fmt(v * p, r.dec)}<span style={{fontSize: 50, fontWeight: 700}}>{r.unit ? ` ${r.unit}` : ''}</span>
              </div>
              {r.bars ? <div style={{marginTop: 16, width: 360, height: 18, borderRadius: 9, background: 'rgba(255,255,255,0.1)'}}>
                <div style={{width: `${(v / maxV) * 100 * p}%`, height: '100%', borderRadius: 9, background: tint}} /></div> : null}
            </div>
          );
          return (
            <React.Fragment key={i}>
              <div style={{position: 'absolute', left: 60, right: 60, top: y - 62, textAlign: 'center', opacity: lp, fontFamily: b.font, fontWeight: 600,
                fontSize: 38, letterSpacing: '0.12em', textTransform: 'uppercase', color: b.muted}}>{r.label}</div>
              {cell(r.a, 70, b.white, false)}
              {cell(r.b, W - 70 - colW, b.accent, true)}
            </React.Fragment>
          );
        })}
      </Camera>
      <Sfx name="whoosh" at={6} volume={0.4} />
      <Sfx name="pop" at={12} volume={0.45} />
      {rows.map((_, i) => <Sfx key={i} name="tick" at={26 + i * every + 18} volume={0.5} />)}
    </AbsoluteFill>
  );
};

// ---- StatSlam: one huge number counts up, ring fills, impact + shake on landing -------------------------
// props: value, prefix, suffix, from, label {text, emph}, kicker, dec, icon
export const StatSlam = ({value, from = 0, prefix = '', suffix = '', dec = 0, label, kicker, icon, dur = 90, ring = true, count = true}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  // count=false: the real number slams in at full value (hooks: frame 0 must never read "$0.0M", A8)
  const land = count ? 22 : 8;
  const p = interpolate(frame, [count ? 4 : 0, land], [0, 1], {...clamp, easing: easeOut});
  const v = count ? from + (value - from) * p : value;
  const slam = count ? 1 : 1.5 - 0.5 * p;
  const R = 330;
  const circ = 2 * Math.PI * R;
  const flash = interpolate(frame, [land, land + 8], [0.35, 0], clamp);
  return (
    <AbsoluteFill>
      <Camera dur={dur} push={0.05} shakeAt={land}>
        {ring ? (
          <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
            <circle cx={W / 2} cy={830} r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={26} />
            <circle cx={W / 2} cy={830} r={R} fill="none" stroke={b.accent} strokeWidth={26} strokeLinecap="round"
              strokeDasharray={circ} strokeDashoffset={circ * (1 - p * Math.min(1, value / 100 || 1))} transform={`rotate(-90 ${W / 2} 830)`} />
          </svg>
        ) : null}
        <div style={{position: 'absolute', left: 0, right: 0, top: 830 - 150, display: 'flex', justifyContent: 'center', alignItems: 'baseline',
          fontFamily: b.font, fontWeight: 900, color: b.white, letterSpacing: '-0.04em', transform: `scale(${(1 + flash) * slam})`, filter: count ? 'none' : blurFor(p, 16)}}>
          <span style={{fontSize: 120, color: b.accent}}>{prefix}</span>
          <span style={{fontSize: 290, lineHeight: 1}}>{fmt(v, dec)}</span>
          <span style={{fontSize: 150, color: b.accent}}>{suffix}</span>
        </div>
        {kicker ? <div style={{position: 'absolute', left: 0, right: 0, top: 330, display: 'flex', justifyContent: 'center'}}><Chip text={kicker} at={0} size={38} /></div> : null}
        {icon ? <div style={{position: 'absolute', left: W / 2 - 75, top: 420, transform: `scale(${usePop(land)})`}}><Icon name={icon} size={150} /></div> : null}
        {label ? <div style={{position: 'absolute', left: 60, right: 60, top: 1220, display: 'flex', justifyContent: 'center'}}>
          <Words text={label.text} emph={label.emph || []} at={land + 4} size={label.size || 76} weight={800} /></div> : null}
      </Camera>
      <div style={{position: 'absolute', inset: 0, background: b.accent, opacity: flash * 0.5, mixBlendMode: 'screen'}} />
      <Sfx name="riser" at={land} volume={0.35} />
      <Sfx name="impact" at={land} volume={0.85} />
      {label ? <Sfx name="pop" at={land + 6} volume={0.45} /> : null}
    </AbsoluteFill>
  );
};

// ---- DocFly: real pages of the asset fan out in 3D and flip past, then one page fills the screen
//      and the camera zooms onto a region with a highlight box ------------------------------------------
// props: pages ['pages/p-03.png', ...], focus {page, box [x0,y0,x1,y1] fractions, note}, caption {text, emph}, aspect (h/w)
export const DocFly = ({pages = [], focus, caption, dur = 120, aspect = 1.294}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const pw = 640;
  const ph = pw * aspect;
  const flipEnd = 12 + pages.length * 5;
  const focusAt = flipEnd + 4;
  const zoomAt = focusAt + 14;
  const fp = interpolate(frame, [focusAt, focusAt + 12], [0, 1], {...clamp, easing: easeOut});
  const zp = interpolate(frame, [zoomAt, zoomAt + 16], [0, 1], {...clamp, easing: easeInOut});
  // focus page: grows from the fan to 900 wide, then zooms so the box fills ~90% of the width
  const fw = 560 + 220 * fp;
  const fh = fw * aspect;
  let zoom = 1;
  let tx = 0;
  let ty = 0;
  if (focus && focus.box) {
    const [x0, y0, x1, y1] = focus.box;
    const target = Math.min(3.2, (W * 0.9) / (fw * (x1 - x0)));
    zoom = 1 + (target - 1) * zp;
    const cx = (x0 + x1) / 2 - 0.5;
    const cy = (y0 + y1) / 2 - 0.5;
    tx = -cx * fw * zoom * zp;
    ty = -cy * fh * zoom * zp;
  }
  const boxP = interpolate(frame, [zoomAt + 14, zoomAt + 22], [0, 1], clamp);
  return (
    <AbsoluteFill style={{perspective: 2200}}>
      {pages.map((src, i) => {
        const at = 6 + i * 5;
        const p = interpolate(frame - at, [0, 14], [0, 1], {...clamp, easing: easeOut});
        const gone = interpolate(frame - at, [14, 26], [0, 1], {...clamp, easing: easeInOut});
        if (p <= 0 || gone >= 1 || frame > focusAt + 10) return null;
        const side = i % 2 ? 1 : -1;
        return (
          <Img key={i} src={staticFile(src)} style={{position: 'absolute', left: W / 2 - pw / 2, top: 820 - ph / 2, width: pw, borderRadius: 14,
            boxShadow: '0 30px 80px rgba(0,0,0,0.6)', opacity: Math.min(1, p * 1.5) * (1 - gone),
            transform: `translateZ(${(1 - p) * -900 + gone * 500}px) translateX(${side * (1 - p) * 500 + side * gone * 700}px) rotateY(${side * (1 - p) * 55 - side * gone * 40}deg) rotateZ(${side * (1 - p) * 8}deg)`,
            filter: blurFor(Math.min(p, 1 - gone), 8)}} />
        );
      })}
      {focus ? (
        <div style={{position: 'absolute', left: W / 2 - fw / 2, top: 790 - fh / 2, width: fw, height: fh, opacity: fp,
          transform: `translate(${tx}px, ${ty}px) scale(${zoom}) rotateX(${(1 - fp) * 25}deg)`, transformOrigin: 'center center'}}>
          <Img src={staticFile(focus.page)} style={{width: '100%', height: '100%', borderRadius: 16, boxShadow: '0 40px 100px rgba(0,0,0,0.65)'}} />
          {focus.box ? (
            <div style={{position: 'absolute', left: `${focus.box[0] * 100}%`, top: `${focus.box[1] * 100}%`, width: `${(focus.box[2] - focus.box[0]) * 100}%`,
              height: `${(focus.box[3] - focus.box[1]) * 100}%`, border: `${4 / zoom}px solid ${b.accent}`, borderRadius: 10 / zoom,
              boxShadow: `0 0 0 ${2000 * boxP}px rgba(0,0,0,${0.55 * boxP})`, opacity: boxP}} />
          ) : null}
        </div>
      ) : null}
      {caption ? <div style={{position: 'absolute', left: 0, right: 0, top: 1300, height: 200, display: 'flex', justifyContent: 'center', alignItems: 'center',
        background: `rgba(0,0,0,${0.88 * interpolate(frame - (caption.at ?? 4), [0, 6], [0, 1], clamp)})`}}>
        <Words text={caption.text} emph={caption.emph || []} at={caption.at ?? 4} size={caption.size || 76} weight={800} pill={caption.pill} /></div> : null}
      {pages.map((_, i) => <Sfx key={i} name="whip" at={6 + i * 5 + 4} volume={0.28} />)}
      {focus ? <Sfx name="whoosh" at={focusAt + 2} volume={0.45} /> : null}
      {focus && focus.box ? <Sfx name="click" at={zoomAt + 14} volume={0.5} /> : null}
    </AbsoluteFill>
  );
};

// ---- CTA: the guide's real cover floats in 3D, label chip, title, a button gets tapped -------------------
// props: cover, chip, title {text, emph}, button, sub, logo
export const CTA = ({cover, clip, chip = 'Free guide', title, button = 'Download the guide', sub, logo, dur = 150, aspect = 1.294}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const cp = interpolate(frame, [0, 16], [0, 1], {...clamp, easing: easeOut});
  const float = Math.sin(frame / 14) * 10;
  const cw = 470;
  const btnAt = 34;
  const tapAt = 56;
  const bp = usePop(btnAt);
  const press = frame >= tapAt && frame < tapAt + 5 ? 0.94 : 1;
  const cursor = interpolate(frame, [tapAt - 16, tapAt], [0, 1], {...clamp, easing: easeOut});
  const ripple = interpolate(frame, [tapAt, tapAt + 16], [0, 1], clamp);
  const arrow = Math.sin(Math.max(0, frame - tapAt) / 4) * 10;
  return (
    <AbsoluteFill style={{perspective: 1800}}>
      {clip ? (
        <div style={{position: 'absolute', left: 70, top: 340 + float, width: W - 140, height: (W - 140) * 9 / 16, opacity: cp, borderRadius: 26, overflow: 'hidden',
          boxShadow: '0 40px 100px rgba(0,0,0,0.7), 0 0 120px rgba(255,59,47,0.25)', transform: `translateY(${(1 - cp) * 300}px) rotateX(${(1 - cp) * 20}deg)`}}>
          <OffthreadVideo src={staticFile(clip)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(0,0,0,0.45), rgba(0,0,0,0) 50%)'}} />
          <div style={{position: 'absolute', left: '50%', top: '50%', width: 150, height: 150, marginLeft: -75, marginTop: -75, borderRadius: 75,
            background: 'rgba(0,0,0,0.55)', border: `4px solid ${b.white}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            transform: `scale(${popAt(frame, 30, 14)})`}}><Icon name="play" size={70} color={b.white} style={{marginLeft: 10}} /></div>
          <div style={{position: 'absolute', left: 26, top: 22}}><Chip text={chip} at={10} size={34} /></div>
        </div>
      ) : (
      <div style={{position: 'absolute', left: W / 2 - cw / 2, top: 300 + float, width: cw, opacity: cp,
        transform: `translateY(${(1 - cp) * 300}px) rotateY(${-18 + cp * 8}deg) rotateX(${6 - cp * 2}deg) rotateZ(${-3 * (1 - cp)}deg)`}}>
        <Img src={staticFile(cover)} style={{width: '100%', borderRadius: 10, boxShadow: '30px 40px 90px rgba(0,0,0,0.7), 0 0 120px rgba(255,59,47,0.25)'}} />
        <div style={{position: 'absolute', left: -30, top: -28}}><Chip text={chip} at={10} size={36} /></div>
      </div>
      )}
      {title ? <div style={{position: 'absolute', left: 60, right: 60, top: clip ? 340 + (W - 140) * 9 / 16 + 70 : 300 + cw * aspect + 50, display: 'flex', justifyContent: 'center'}}>
        <Words text={title.text} emph={title.emph || []} at={18} size={title.size || 68} weight={800} stagger={2} /></div> : null}
      <div style={{position: 'absolute', left: 0, right: 0, top: 1300, display: 'flex', justifyContent: 'center'}}>
        <div style={{position: 'relative', transform: `scale(${bp * press})`, display: 'flex', alignItems: 'center', gap: 22, background: b.accent, color: b.ink,
          fontFamily: b.font, fontWeight: 800, fontSize: 54, padding: '30px 54px', borderRadius: 80, boxShadow: '0 16px 50px rgba(255,59,47,0.45)'}}>
          <div style={{transform: `translateY(${arrow}px)`}}><Icon name={clip ? 'play' : 'arrow-down-to-line'} size={58} color={b.ink} /></div>
          {button}
          {frame >= tapAt ? <div style={{position: 'absolute', left: '62%', top: '50%', width: 40, height: 40, marginLeft: -20, marginTop: -20, borderRadius: 20,
            border: `4px solid ${b.white}`, transform: `scale(${1 + ripple * 6})`, opacity: 1 - ripple}} /> : null}
        </div>
      </div>
      {cursor > 0 ? <div style={{position: 'absolute', left: W * 0.62 + (1 - cursor) * 260, top: 1350 + (1 - cursor) * 240, transform: `scale(${press})`}}>
        <Icon name="mouse-pointer-click" size={96} color={b.white} style={{filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.7))'}} /></div> : null}
      {sub ? <div style={{position: 'absolute', left: 60, right: 60, top: 1430, display: 'flex', justifyContent: 'center'}}>
        <Words text={sub} at={tapAt + 8} size={40} weight={500} mode="rise" color={b.muted} /></div> : null}
      {logo ? <Img src={staticFile(logo)} style={{position: 'absolute', left: W / 2 - 170, top: 1490 - 0, width: 340, opacity: useIn(tapAt + 14, 8)}} /> : null}
      <Sfx name="click" at={tapAt} volume={0.7} />
    </AbsoluteFill>
  );
};

// ---- PhotoPunch: a real photo full screen with a held zoom and a kinetic caption low ------------------------
export const PhotoPunch = ({imagery = "generic", photo, lines = [], kicker, dur = 75, position = 'center'}) => (
  <AbsoluteFill>
    <Photo src={photo} imagery={imagery} dur={dur} from={1.15} to={1.02} dim={0.4} position={position} />
    <Stack top={1010} gap={12}>
      {kicker ? <Chip text={kicker} at={0} size={34} /> : null}
      {lines.map((ln, i) => <Words key={i} text={ln.text} emph={ln.emph || []} at={4 + i * 10} size={ln.size || 104} pill={ln.pill} />)}
    </Stack>
    <Sfx name="whoosh" at={2} volume={0.4} />
    {lines.map((_, i) => <Sfx key={i} name="pop" at={6 + i * 10} volume={0.45} />)}
  </AbsoluteFill>
);

// ---- LogoOpen: the customer's real logo on a white card pops in, headline below ----
// props: logo, lines [{text, emph, size}], kicker
export const LogoOpen = ({logo, lines = [], kicker, dur = 105, card = 420}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const p = usePop(0);
  const float = Math.sin(frame / 18) * 8;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: W / 2 - card / 2, top: 420 + float, width: card, height: card, borderRadius: 48, background: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${p})`, boxShadow: '0 30px 90px rgba(0,0,0,0.6), 0 0 140px rgba(255,59,47,0.3)'}}>
        <Img src={staticFile(logo)} style={{width: card * 0.78, height: card * 0.78, objectFit: 'contain'}} />
      </div>
      <Stack top={420 + card + 80} gap={18}>
        {kicker ? <Chip text={kicker} at={8} size={38} /> : null}
        {lines.map((ln, i) => <Words key={i} text={ln.text} emph={ln.emph || []} at={14 + i * 12} size={ln.size || 100} pill={ln.pill} />)}
      </Stack>
      <Sfx name="impact" at={0} volume={0.5} />
    </AbsoluteFill>
  );
};

// ---- Footage: a real clip from a longer film, already 9:16 and face-centred (subtitles burned in), with its own sound ----
// props: clip, from (s), volume, kicker
export const Footage = ({clip, from = 0, volume = 1, kicker, dur = 150}) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <OffthreadVideo src={staticFile(clip)} startFrom={Math.round(from * fps)} volume={volume} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      {kicker ? <div style={{position: 'absolute', left: 60, top: 270}}><Chip text={kicker} at={4} size={36} /></div> : null}
    </AbsoluteFill>
  );
};

// ---- ReadingWindow: a Claude-style window "reads" lines of fake placeholder text (grey bars), a scan marks each line ----
// Decorative only: no words, numbers or claims. Sits in the top zone so it can be used behind him (bg_swap).
// props: title (window title, a name he said), rows (count), top (px). No logo or brand mark of any model: a plain dot only.
// With rows 8 and top 100 the window ends near y 590, above the face (face top about y 700), and he is cut out in front of it.
export const ReadingWindow = ({title = 'Claude', rows = 8, top = 100, dur = 90}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  const widths = [0.92, 0.78, 0.86, 0.55, 0.9, 0.68, 0.82, 0.48, 0.74, 0.88, 0.6];
  const enter = interpolate(frame, [0, 10], [0, 1], {...clamp, easing: easeOut});
  const cur = Math.max(0, Math.floor((frame - 8) / 8)); // the line being read now
  const wW = 900, rowH = 46;
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', left: (W - wW) / 2, top: top + (1 - enter) * -60, width: wW, opacity: enter, transform: `scale(${0.94 + 0.06 * enter})`,
        borderRadius: 28, background: '#16161d', border: `2px solid ${b.accent}`, overflow: 'hidden', boxShadow: '0 24px 70px rgba(0,0,0,0.55)'}}>
        <div style={{height: 64, display: 'flex', alignItems: 'center', gap: 12, padding: '0 24px', background: '#1f1f29'}}>
          <div style={{width: 16, height: 16, borderRadius: 8, background: '#ff6b5b'}} />
          <div style={{width: 16, height: 16, borderRadius: 8, background: '#ffd43b'}} />
          <div style={{width: 16, height: 16, borderRadius: 8, background: '#7bd88f'}} />
          <div style={{flex: 1, textAlign: 'center', color: '#fff', fontFamily: b.font, fontWeight: 700, fontSize: 30, direction: 'ltr', paddingRight: 60}}>
            <span style={{display: 'inline-block', width: 14, height: 14, borderRadius: 7, background: b.accent, marginRight: 12}} />{title}
          </div>
        </div>
        <div style={{padding: '30px 36px', direction: 'ltr'}}>
          {Array.from({length: rows}).map((_, i) => {
            const appear = interpolate(frame - i * 2, [0, 6], [0, 1], {...clamp, easing: easeOut});
            const read = frame >= 8 + i * 8;
            const now = i === cur && frame >= 8 && i < rows;
            const fill = interpolate(frame - (8 + i * 8), [0, 8], [0, 1], clamp);
            const w = widths[i % widths.length] * (wW - 72);
            return (
              <div key={i} style={{height: rowH, display: 'flex', alignItems: 'center', opacity: appear}}>
                <div style={{position: 'relative', width: w, height: 18, borderRadius: 9, background: '#3a3a48', overflow: 'hidden'}}>
                  <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${read ? fill * 100 : 0}%`, background: b.accent, opacity: 0.85, borderRadius: 9}} />
                </div>
                {now ? <div style={{marginLeft: 14, width: 16, height: 16, borderRadius: 8, background: b.accent}} /> : null}
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const SCENES = {ReadingWindow, IconSwarm, Kinetic, IconList, Compare, StatSlam, DocFly, CTA, PhotoPunch, LogoOpen, Footage};

// ---- transition wrapper: whip in from below with blur, whip out upward -----------------------------------
export const Shell = ({children, dur, enter = 'whip', exit = 'whip'}) => {
  const frame = useCurrentFrame();
  const b = useBrand();
  if (b.strict) {
    // organic: a clean slide, no blur or scale effects between sections (guide p95)
    const ip = enter === 'cut' ? 1 : interpolate(frame, [0, 8], [0, 1], {...clamp, easing: easeOut});
    const op = exit === 'cut' ? 0 : interpolate(frame, [dur - 6, dur], [0, 1], {...clamp, easing: Easing_in});
    return <AbsoluteFill style={{transform: `translateX(${(1 - ip) * 1080 - op * 1080}px)`}}>{children}</AbsoluteFill>;
  }
  const ip = enter === 'cut' ? 1 : interpolate(frame, [0, 12], [0, 1], {...clamp, easing: easeOut});
  const op = exit === 'cut' ? 0 : interpolate(frame, [dur - 8, dur], [0, 1], {...clamp, easing: Easing_in});
  const y = (1 - ip) * 260 - op * 320;
  const s = 1 - (1 - ip) * 0.06 + op * 0.04;
  return (
    <AbsoluteFill style={{transform: `translateY(${y}px) scale(${s})`, filter: `blur(${(1 - ip) * 22 + op * 26}px)`, opacity: Math.min(1, ip * 1.6) * (1 - op * 0.6)}}>
      {children}
    </AbsoluteFill>
  );
};
const Easing_in = (t) => t * t * t;
