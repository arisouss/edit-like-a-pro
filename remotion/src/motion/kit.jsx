// Shared motion kit: the building blocks every scene uses. One copy, used by edit-like-a-pro and the reels skill.
// Motion rules (motion-rules.md): fast in, slow landing, never linear, slight overshoot on pops,
// motion blur on anything that travels, one thing at a time, sound on every arrival.
import React, {createContext, useContext} from 'react';
import {Audio, Img, Sequence, interpolate, Easing, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export const W = 1080;
export const H = 1920;
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};

// ---- brand ---------------------------------------------------------------
const DEFAULT_BRAND = {
  font: 'Roboto, Arial, sans-serif', ink: '#000000', white: '#FFFFFF', accent: '#FF3B2F', cta: '#FF3B2F',
  soft: 'rgba(255,59,47,0.16)', muted: '#8A949E', warn: '#FFB020', ok: '#7BD88F',
};
export const BrandContext = createContext(DEFAULT_BRAND);
export const useBrand = () => ({...DEFAULT_BRAND, ...useContext(BrandContext)});

// ---- easing helpers --------------------------------------------------------
export const easeOut = Easing.bezier(0.16, 1, 0.3, 1); // expo-like: fast in, slow landing
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

// 0 -> 1 with a small overshoot, over ~n frames, starting at frame `at`
export const usePop = (at = 0, damping = 11, mass = 0.6) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - at, fps, config: {damping, mass, stiffness: 180}});
};

// same as usePop but a plain function: safe inside loops and conditions (React hook rules, G56)
export const popAt = (frame, fps, at = 0, damping = 11, mass = 0.6) =>
  spring({frame: frame - at, fps, config: {damping, mass, stiffness: 180}});

// 0 -> 1 eased, no overshoot
export const useIn = (at = 0, n = 10, ease = easeOut) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [at, at + n], [0, 1], {...clamp, easing: ease});
};

// motion blur proxy: blur in px proportional to how fast p is changing
export const blurFor = (p, max = 18) => `blur(${Math.max(0, (1 - p) * max).toFixed(2)}px)`;

// ---- sound -------------------------------------------------------------------
// Place a sound so that its PEAK lands on frame `at` (lead = frames before the peak in the file).
const LEAD = {whoosh: 6, whip: 3, pop: 0, tick: 0, click: 0, impact: 0, riser: 34, ding: 0, swoosh_out: 4};
export const Sfx = ({name, at = 0, volume = 0.6}) => {
  const start = Math.max(0, at - (LEAD[name] || 0));
  return (
    <Sequence from={start} durationInFrames={60} layout="none">
      <Audio src={staticFile(`sfx/${name}.wav`)} volume={volume} />
    </Sequence>
  );
};

// ---- icons (Lucide, ISC licence; recoloured with a CSS mask so they take any brand colour) ----
export const Icon = ({name, size = 120, color, style}) => {
  const b = useBrand();
  const url = `url(${staticFile(`icons/${name.includes('.') ? name : name + '.svg'}`)})`;
  return (
    <div style={{width: size, height: size, background: color || b.accent, WebkitMaskImage: url, maskImage: url,
      WebkitMaskSize: 'contain', maskSize: 'contain', WebkitMaskRepeat: 'no-repeat', maskRepeat: 'no-repeat',
      WebkitMaskPosition: 'center', maskPosition: 'center', ...style}} />
  );
};

// icon inside a soft round badge: reads at phone size on any background
export const IconBadge = ({name, size = 150, color, bg, ring}) => {
  const b = useBrand();
  return (
    <div style={{width: size, height: size, borderRadius: size / 2, background: bg || 'rgba(255,255,255,0.08)',
      border: `3px solid ${ring || 'rgba(255,59,47,0.55)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
      boxShadow: '0 10px 40px rgba(0,0,0,0.45)'}}>
      <Icon name={name} size={size * 0.52} color={color || b.accent} />
    </div>
  );
};

// ---- text ----------------------------------------------------------------------
// One line, words arrive one by one (or all together with stagger 0). Words listed in `emph` get the accent.
// style 'slam': scale 1.35 -> 1 with blur. style 'rise': slide up from a mask. style 'type': appear per letter.
export const Words = ({text, at = 0, stagger = 3, size = 120, weight = 900, emph = [], color, align = 'center',
  mode = 'slam', pill = false, upper = false, lineHeight = 1.02, maxWidth = 960}) => {
  const b = useBrand();
  const frame = useCurrentFrame();
  const words = text.split(' ');
  const isEmph = (w) => emph.some((e) => w.toLowerCase().replace(/[^\w%$~.]/g, '').startsWith(e.toLowerCase()));
  return (
    <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: align === 'center' ? 'center' : 'flex-start',
      maxWidth, fontFamily: b.font, fontWeight: weight, fontSize: size, lineHeight, letterSpacing: '-0.025em',
      textTransform: upper ? 'uppercase' : 'none', columnGap: size * 0.26}}>
      {words.map((w, i) => {
        const t0 = at + i * stagger;
        const local = frame - t0;
        if (local < 0) return <span key={i} style={{opacity: 0}}>{w}</span>;
        const p = interpolate(local, [0, 6], [0, 1], {...clamp, easing: easeOut});
        const e = isEmph(w);
        let tr = '';
        if (mode === 'slam') tr = `scale(${1.35 - 0.35 * p})`;
        if (mode === 'rise') tr = `translateY(${(1 - p) * 60}%)`;
        const st = {display: 'inline-block', transform: tr, filter: mode === 'type' ? 'none' : blurFor(p, 14),
          opacity: mode === 'type' ? 1 : Math.min(1, p * 2), color: e ? (pill ? b.ink : b.accent) : (color || b.white),
          textShadow: e && pill ? 'none' : '0 4px 30px rgba(0,0,0,0.55)'};
        if (e && pill) Object.assign(st, {background: b.accent, padding: `0 ${size * 0.16}px`, borderRadius: size * 0.16});
        if (mode === 'type') {
          const n = Math.floor(interpolate(local, [0, w.length * 1.2], [0, w.length], clamp));
          return <span key={i} style={st}>{w.slice(0, n)}</span>;
        }
        return <span key={i} style={st}>{w}</span>;
      })}
    </div>
  );
};

// small rounded label ("FREE GUIDE", "CASE STUDY", "p.6")
export const Chip = ({text, at = 0, color, bg, size = 40}) => {
  const b = useBrand();
  const p = usePop(at);
  return (
    <div style={{display: 'inline-block', transform: `scale(${p})`, fontFamily: b.font, fontWeight: 700, fontSize: size,
      letterSpacing: '0.08em', textTransform: 'uppercase', color: color || b.ink, background: bg || b.accent,
      padding: `${size * 0.28}px ${size * 0.6}px`, borderRadius: size}}>{text}</div>
  );
};

// ---- camera ------------------------------------------------------------------
// slow push-in across a scene plus an optional shake burst at `shakeAt` (impacts)
export const Camera = ({children, push = 0.05, dur = 90, shakeAt = null}) => {
  const frame = useCurrentFrame();
  const s = 1 + interpolate(frame, [0, dur], [0, push], {...clamp, easing: easeInOut});
  let dx = 0;
  let dy = 0;
  if (shakeAt !== null && frame >= shakeAt && frame < shakeAt + 9) {
    const k = 1 - (frame - shakeAt) / 9;
    dx = Math.sin(frame * 2.7) * 16 * k;
    dy = Math.cos(frame * 3.1) * 12 * k;
  }
  return <div style={{position: 'absolute', inset: 0, transform: `translate(${dx}px, ${dy}px) scale(${s})`}}>{children}</div>;
};

// a real photo, Ken Burns drift, darkened, with the brand's soft blue wash
export const Photo = ({src, dur = 90, from = 1.08, to = 1.0, x0 = 0, x1 = 0, dim = 0.45, wash, fit = 'cover', position = 'center', imagery = 'generic'}) => {
  const frame = useCurrentFrame();
  const brand = useBrand();
  // a soft accent wash over generic photos: only when the brand profile asks for it (taste Rule 45)
  // generic imagery gets the wash; product imagery stays in natural colors
  if (wash === undefined) wash = !!brand.photo_wash && imagery !== 'product';
  const p = interpolate(frame, [0, dur], [0, 1], {...clamp, easing: easeInOut});
  const s = from + (to - from) * p;
  const x = x0 + (x1 - x0) * p;
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: fit, objectPosition: position,
        transform: `translateX(${x}px) scale(${s})`}} />
      {wash ? <div style={{position: 'absolute', inset: 0, background: brand.accent, opacity: brand.photo_wash_opacity ?? 0.5, mixBlendMode: 'soft-light'}} /> : null}
      <div style={{position: 'absolute', inset: 0, background: `linear-gradient(to bottom, rgba(0,0,0,${dim}) 0%, rgba(0,0,0,${dim * 0.55}) 45%, rgba(0,0,0,${Math.min(0.92, dim + 0.35)}) 100%)`}} />
    </div>
  );
};

// A brand profile with "strict": true follows its guide to the letter:
// square corners, no glows or drop shadows on graphics.
export const StrictStyle = () => {
  const b = useBrand();
  if (!b.strict) return null;
  return <style>{`.the brand's own root * { border-radius: 0 !important; box-shadow: none !important; }`}</style>;
};
