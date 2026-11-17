// Rule 42: the effects layer on top of the talking-head edit, from $WD/fx.json (checked by s06b_fx.py).
// Kinds:
//   icon_pop     icons (and short labels) pop into the zone above his head, each on its spoken word
//   behind_words big words placed BEHIND his head (needs subject.webm from cutout.py)
//   bg_swap      his background is replaced: the brand backdrop, a real image (optionally scrolling) or a scene behind him
//   takeover     he leaves the frame and a full-screen scene from the motion kit plays (voice and captions continue)
//   stat         a number counts up in the top zone
// Every fx places its own sound from the shared kit. Captions still draw on top of everything.
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile, useCurrentFrame, interpolate} from 'remotion';
import {BrandContext, clamp, easeOut, popAt, Sfx, IconBadge, Words, Icon, Photo} from './motion/kit';
import {Backdrop, SCENES} from './motion/scenes';

const H = 1920;
const FX_FONT = {f: 'Roboto'}; // set from the brand profile on render
const W = 1080;

// same framing as HeadShot at this moment, so the cut-out body sits exactly on the base video
const useShotScale = (shots, fps, from) => {
  const frame = useCurrentFrame();
  const t = (from + frame) / fps;
  const s = shots.find((x) => t >= x.start && t < x.end);
  return s && s.scale ? s.scale : 1;
};

const Subject = ({fx, fps, shots, geom}) => {
  const from = Math.round(fx.start * fps);
  const sc = useShotScale(shots, fps, from);
  const fc = geom.face_centre;
  return (
    <AbsoluteFill style={{transform: `scale(${sc})`, transformOrigin: `${fc.x * 100}% ${fc.y * 100}%`}}>
      <OffthreadVideo src={staticFile('subject.webm')} startFrom={from} muted transparent style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
  );
};

const Base = ({fx, fps, shots, geom}) => {
  const from = Math.round(fx.start * fps);
  const sc = useShotScale(shots, fps, from);
  const fc = geom.face_centre;
  return (
    <AbsoluteFill style={{transform: `scale(${sc})`, transformOrigin: `${fc.x * 100}% ${fc.y * 100}%`}}>
      <OffthreadVideo src={staticFile('tight.mp4')} startFrom={from} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
  );
};

const NewBackground = ({bg, dur}) => {
  const frame = useCurrentFrame();
  if (bg.image) {
    if (bg.scroll) {
      // a tall real capture scrolls slowly behind him
      const y = interpolate(frame, [0, dur], [0, -(bg.travel || 900)], {...clamp, easing: easeOut});
      return (
        <AbsoluteFill style={{background: '#000', overflow: 'hidden'}}>
          <Img src={staticFile(bg.image)} style={{position: 'absolute', left: 0, top: y, width: W, filter: 'brightness(0.75)'}} />
        </AbsoluteFill>
      );
    }
    return <Photo src={bg.image} dur={dur} dim={0.25} wash={bg.wash !== false} />;
  }
  if (bg.scene) {
    const C = SCENES[bg.scene];
    return <AbsoluteFill><Backdrop pattern={bg.pattern} /><C {...(bg.props || {})} dur={dur} /></AbsoluteFill>;
  }
  return <Backdrop pattern={bg.pattern} speed={bg.speed ?? 1.2} />;
};

const IconPop = ({fx, fps, brand}) => {
  const frame = useCurrentFrame();
  const n = fx.icons.length;
  const size = n > 3 ? 160 : 200;
  const total = Math.round((fx.end - fx.start) * fps);
  const out = interpolate(frame, [total - 5, total], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: 40, right: 40, top: H * (fx.top ?? 0.09), display: 'flex', justifyContent: 'center', gap: n > 3 ? 26 : 50, opacity: out}}>
      {fx.icons.map((ic, i) => {
        const at = Math.round((ic.at - fx.start) * fps);
        if (frame < at) return <div key={i} style={{width: size + 20}} />;
        const p = popAt(frame, fps, at);
        return (
          <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, width: size + 20, transform: `scale(${p}) translateY(${(1 - p) * 40}px)`}}>
            <IconBadge name={ic.name} size={size} bg={brand.accent} ring="rgba(255,255,255,0.9)" color="#FFFFFF" />
            {ic.label ? <div style={{fontFamily: `"${FX_FONT.f}", Arial, sans-serif`, fontWeight: 700, fontSize: 48, color: '#fff', textAlign: 'center',
              textShadow: '0 2px 12px rgba(0,0,0,0.8)', lineHeight: 1.05}}>{ic.label}</div> : null}
          </div>
        );
      })}
      {fx.icons.map((ic, i) => <Sfx key={i} name="pop" at={Math.round((ic.at - fx.start) * fps)} volume={0.45} />)}
    </div>
  );
};

const Stat = ({fx, fps}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [2, 20], [0, 1], {...clamp, easing: easeOut});
  const v = (fx.from || 0) + (fx.value - (fx.from || 0)) * p;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: H * (fx.top ?? 0.08), textAlign: 'center', fontFamily: `"${FX_FONT.f}", Arial, sans-serif`,
      fontWeight: 700, color: '#fff', textShadow: '0 4px 30px rgba(0,0,0,0.7)'}}>
      <div style={{fontSize: 230, lineHeight: 1}}>{fx.prefix || ''}{Math.round(v)}<span style={{fontSize: 120}}>{fx.suffix || ''}</span></div>
      {fx.label ? <div style={{fontSize: 56}}>{fx.label}</div> : null}
      {fx.sound === 'one' ? null : <Sfx name="riser" at={20} volume={0.3} />}
      <Sfx name="impact" at={20} volume={0.6} />
    </div>
  );
};

export const FxLayer = ({fx = [], fps, shots, geom, brand, hasCutout, faceBox}) => {
  // top of his hair, from his own measured face box [x, y, w, h] (intake.json), not the study geometry
  const headTop = faceBox ? (faceBox[1] - 0.45 * faceBox[3]) * H : (geom.face_centre.y - 0.12) * H;
  FX_FONT.f = brand.font;
  const kitBrand = {font: `"${brand.font}", Arial, sans-serif`, ink: brand.ink, white: brand.white, accent: brand.accent, muted: brand.muted, photo_wash: !!brand.photo_wash, photo_wash_opacity: brand.photo_wash_opacity, strict: !!brand.strict};
  return (
    <BrandContext.Provider value={kitBrand}>
      {fx.map((x, i) => {
        const from = Math.round(x.start * fps);
        const dur = Math.max(1, Math.round((x.end - x.start) * fps));
        let body = null;
        if (x.kind === 'icon_pop') body = <IconPop fx={x} fps={fps} brand={brand} />;
        if (x.kind === 'stat') body = <Stat fx={x} fps={fps} />;
        if (x.kind === 'takeover') {
          const C = SCENES[x.scene];
          body = (
            <AbsoluteFill>
              <Backdrop pattern={x.pattern} />
              <C {...(x.props || {})} dur={dur} />
              <Sfx name="whip" at={0} volume={0.4} />
            </AbsoluteFill>
          );
        }
        if (x.kind === 'behind_words' && hasCutout) {
          body = (
            <AbsoluteFill>
              <Base fx={x} fps={fps} shots={shots} geom={geom} />
              <div style={{position: 'absolute', left: 30, right: 30, top: x.top ?? Math.max(240, headTop - 0.72 * (x.size || 210)), display: 'flex', justifyContent: 'center'}}>
                <Words text={x.text} emph={x.emph || []} at={x.at ? Math.round((x.at - x.start) * fps) : 2} size={x.size || 210} stagger={4} upper={x.upper !== false} />
              </div>
              <Subject fx={x} fps={fps} shots={shots} geom={geom} />
              <Sfx name="whoosh" at={2} volume={0.4} />
            </AbsoluteFill>
          );
        }
        if (x.kind === 'bg_swap' && hasCutout) {
          body = (
            <AbsoluteFill>
              <NewBackground bg={x.bg || {}} dur={dur} />
              <Subject fx={x} fps={fps} shots={shots} geom={geom} />
              <Sfx name="whoosh" at={0} volume={0.45} />
            </AbsoluteFill>
          );
        }
        if (!body) return null;
        return <Sequence key={`fx${i}`} from={from} durationInFrames={dur} name={`fx ${x.kind}`}>{body}</Sequence>;
      })}
    </BrandContext.Provider>
  );
};
