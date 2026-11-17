// The edit, built from props.json. Mechanics from the style guide, look from this video's brand profile (brands/*.json).
// Nothing here is styled after the study creator: colors and font come from props.brand only.
import React, {useEffect, useState} from 'react';
import {
  AbsoluteFill, Sequence, OffthreadVideo, Audio, Img, staticFile,
  useCurrentFrame, interpolate, Easing, delayRender, continueRender,
} from 'remotion';
import data from './props.json';
import {FxLayer} from './FxLayer';

const {fps, shots, graphics, pages, title, end_logo: endLogo, brand, geom, fx = [], cutout = false, face_box: faceBox = null} = data;
const f = (t) => Math.round(t * fps);
const H = 1920;
const W = 1080;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const FONT = `"${data.brand.font}", Arial, sans-serif`;
// Hebrew and other right-to-left languages (props.rtl, set by s08_build from words.json): text runs right to left, no negative letter spacing
const RTL = !!data.rtl;
const BIDI = RTL ? {direction: 'rtl', unicodeBidi: 'plaintext'} : {};
const SHADOW = '0 2px 2px rgba(8,9,11,0.55), 0 4px 22px rgba(8,9,11,0.75), 0 0 3px rgba(8,9,11,0.6)';

const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    // fonts of this video's brand profile (brands/*.json, taste Rule 45)
    const faces = Object.entries(data.brand.font_files).map(([w, file]) => new FontFace(data.brand.font, `url(${staticFile(file)})`, {weight: w}));
    Promise.all(faces.map((x) => x.load())).then((fs) => {
      fs.forEach((x) => document.fonts.add(x));
      continueRender(handle);
    });
  }, [handle]);
};

// ---- video layers -------------------------------------------------------
const HeadShot = ({shot}) => {
  const fc = geom.face_centre;
  return (
    <AbsoluteFill style={{transform: `scale(${shot.scale})`, transformOrigin: `${fc.x * 100}% ${fc.y * 100}%`}}>
      <OffthreadVideo src={staticFile('tight.mp4')} startFrom={f(shot.start)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    </AbsoluteFill>
  );
};

const Plate = ({shot}) => {
  const item = shot.asset ? staticFile(shot.asset) : null;
  return (
    <AbsoluteFill style={{background: brand.plate}}>
      {shot.layout === 'D' && item && (
        <div style={{position: 'absolute', left: W * 0.07, top: H * 0.16, width: W * 0.86, height: H * 0.56, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
          <Img src={item} style={{maxWidth: '100%', maxHeight: '100%', borderRadius: 36, boxShadow: '0 20px 60px rgba(8,9,11,0.18)'}} />
        </div>
      )}
      {shot.layout === 'E' && (
        <div style={{position: 'absolute', left: W * 0.19, top: H * 0.22, width: W * 0.62, height: H * 0.52, borderRadius: 40, overflow: 'hidden', boxShadow: '0 20px 60px rgba(8,9,11,0.22)'}}>
          <OffthreadVideo src={staticFile('tight.mp4')} startFrom={f(shot.start)} muted style={{width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.0)'}} />
        </div>
      )}
    </AbsoluteFill>
  );
};

// ---- captions: one short caption at a time, same row in every layout -------
const Caption = () => {
  const frame = useCurrentFrame();
  const t = frame / fps;
  const page = pages.find((p) => t >= p.start && t < p.end);
  if (!page) return null;
  const shot = shots.find((s) => t >= s.start && t < s.end);
  const onPlate = shot && (shot.layout === 'D' || shot.layout === 'E');
  const local = frame - f(page.start);
  const op = 1;
  const sc = interpolate(local, [0, 3], [0.94, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const y = geom.caption_band.centre * H;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: y - 70, height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: op, transform: `scale(${sc})`}}>
      <span style={{
        fontFamily: FONT, fontWeight: 700, fontSize: 88, lineHeight: 1.1, letterSpacing: RTL ? 0 : '-0.01em', ...BIDI,
        color: onPlate ? brand.ink : brand.white, textShadow: onPlate ? 'none' : SHADOW,
        background: page.emph ? brand.accent : 'transparent', padding: page.emph ? '4px 28px' : 0, borderRadius: 22,
      }}>{page.text}</span>
    </div>
  );
};

// ---- title, graphics, end logo ---------------------------------------------
const pop = (frame, n) => interpolate(frame, [0, n], [0.4, 1], {...clamp, easing: Easing.out(Easing.cubic)});

const Title = () => {
  const frame = useCurrentFrame();
  const total = f(title.end) - f(title.start);
  const op = interpolate(frame, [0, 2, total - 3, total], [0, 1, 1, 0], clamp);
  const y0 = geom.title_block.y0 * H;
  return (
    <>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: H * 0.36, opacity: op, background: 'linear-gradient(to bottom, rgba(8,9,11,${title.scrim ?? 0.5}), rgba(8,9,11,0))'}} />
      <div style={{position: 'absolute', left: 60, right: 60, top: y0, textAlign: 'center', opacity: op, fontFamily: FONT, ...BIDI}}>
        <div style={{fontWeight: 700, fontSize: title.size1 ?? 78, lineHeight: 1.08, color: brand.white, textShadow: SHADOW}}>{title.line1}</div>
        {title.line2 ? <div style={{fontWeight: 700, fontSize: title.size2 ?? 68, lineHeight: 1.12, marginTop: 10, color: title.line2_color ?? brand.accent_soft, textShadow: SHADOW}}>{title.line2}</div> : null}
      </div>
    </>
  );
};

const Graphic = ({g}) => {
  const frame = useCurrentFrame();
  const total = f(g.end) - f(g.start);
  const enter = g.enter_frames;
  const exit = g.exit_frames;
  const opIn = interpolate(frame, [0, Math.max(1, Math.min(enter, 2))], [0, 1], clamp);
  const opOut = interpolate(frame, [total - exit, total], [1, 0], clamp);
  const scIn = g.anim === 'pop' ? pop(frame, enter) : 1;
  const scOut = interpolate(frame, [total - exit, total], [1, 0.9], clamp);
  const style = {position: 'absolute', opacity: opIn * opOut, transform: `scale(${scIn * scOut})`, fontFamily: FONT};
  const zone0 = g.zone[0] * H;
  if (g.kind === 'keyword_text') {
    return <div style={{...style, ...BIDI, left: 60, right: 60, top: H * 0.15, textAlign: 'center', fontWeight: 700, fontSize: 112, lineHeight: 1.05, color: brand.white, textShadow: SHADOW}}>{g.text}</div>;
  }
  if (g.kind === 'numbered_list') {
    // Rules 39 and 41: a soft card in the top zone, each line pops in on its word, with an optional icon.
    const hasIcons = g.lines.some((ln) => ln.icon);
    return (
      <div style={{position: 'absolute', left: 60, right: 60, top: H * 0.07, padding: '26px 34px', borderRadius: 32, background: brand.strict ? brand.surface : 'rgba(245,246,247,0.94)'  /* guide p43: no see-through backgrounds on organic */, boxShadow: '0 14px 40px rgba(8,9,11,0.28)', opacity: opIn * opOut, fontFamily: FONT, ...BIDI, fontWeight: 700, fontSize: hasIcons ? 54 : 58, lineHeight: 1.2, color: brand.ink}}>
        {g.text ? <div style={{marginBottom: 6}}>{g.text}</div> : null}
        {g.lines.map((ln, i) => {
          const t0 = f(ln.start_rel);
          if (frame < t0) return null;
          const sc = pop(frame - t0, 5);
          return (
            <div key={i} style={{display: 'flex', alignItems: 'center', gap: 22, margin: '6px 0', transform: `scale(${sc})`, transformOrigin: 'left center'}}>
              {hasIcons ? (ln.icon ? <Img src={staticFile(ln.icon)} style={{width: 78, height: 78, objectFit: 'contain'}} /> : <div style={{width: 78, height: 78, borderRadius: 39, background: brand.accent, color: brand.white, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 40}}>{i + 1}</div>) : <span style={{color: brand.accent}}>{i + 1}.</span>}
              <span>{ln.text}</span>
            </div>
          );
        })}
      </div>
    );
  }
  if (!g.asset) return null;
  const src = staticFile(g.asset);
  const maxH = Math.max(120, (g.zone[1] - g.zone[0]) * H);
  if (g.kind === 'photo_insert') {
    return <Img src={src} style={{...style, right: 60, top: zone0 + 40, width: W * 0.22, maxHeight: maxH - 40, objectFit: 'contain', borderRadius: 18, boxShadow: '0 10px 30px rgba(0,0,0,0.35)'}} />;
  }
  if (g.kind === 'logo') {
    return <Img src={src} style={{...style, left: W * 0.5 - (W * g.width_frac) / 2, top: zone0 + 30, width: W * g.width_frac}} />;
  }
  if (g.scroll && g.aspect) {
    // Rule 40: a real full-page capture scrolls inside a fixed card (top to bottom over the hold).
    const cw = W * g.width_frac;
    const imgH = cw * g.aspect;
    const travel = Math.max(0, imgH - maxH);
    const y = interpolate(frame, [Math.min(8, total - 2), Math.max(9, total - exit - 4)], [0, -travel], {...clamp, easing: Easing.inOut(Easing.cubic)});
    return (
      <div style={{...style, left: W * 0.5 - cw / 2, top: zone0, width: cw, height: Math.min(maxH, imgH), overflow: 'hidden', borderRadius: 28, boxShadow: '0 14px 40px rgba(0,0,0,0.35)'}}>
        <Img src={src} style={{position: 'absolute', left: 0, top: y, width: cw}} />
      </div>
    );
  }
  return <Img src={src} style={{...style, left: W * 0.5 - (W * g.width_frac) / 2, top: zone0, width: W * g.width_frac, maxHeight: maxH, objectFit: 'contain', borderRadius: 28, boxShadow: '0 14px 40px rgba(0,0,0,0.35)'}} />;
};

const EndLogo = () => {
  if (!endLogo.asset) return null; // default profile: no logo unless the brand file names one
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 2], [0, 1], clamp);
  return (
    <>
      <div style={{position: 'absolute', left: 0, right: 0, top: 0, height: H * 0.30, opacity: op, background: 'linear-gradient(to bottom, rgba(8,9,11,${title.scrim ?? 0.5}), rgba(8,9,11,0))'}} />
      {/* guide p21: never a shadow or effect on the logo; a solid black band keeps it off the busy video */}
      <div style={{position: 'absolute', left: 0, right: 0, top: H * 0.07, height: 260, background: '#000', opacity: op}} />
      <Img src={staticFile(endLogo.asset)} style={{position: 'absolute', left: W * 0.5 - 230, top: H * 0.07 + 70, width: 460, opacity: op}} />
    </>
  );
};

export const Edit = () => {
  useFonts();
  return (
    <AbsoluteFill className="the brand's own root" style={{background: brand.ink}}>
      {/* strict brand profiles: square corners, no glows or shadows on graphics */}
      {brand.strict ? <style>{`.the brand's own root * { border-radius: 0 !important; box-shadow: none !important; }`}</style> : null}
      <Audio src={staticFile('tight.mp4')} />
      {shots.map((s) => (
        <Sequence key={`v${s.id}`} from={f(s.start)} durationInFrames={Math.max(1, f(s.end) - f(s.start))}>
          {s.layout === 'D' || s.layout === 'E' ? <Plate shot={s} /> : <HeadShot shot={s} />}
        </Sequence>
      ))}
      <Sequence from={f(title.start)} durationInFrames={Math.max(1, f(title.end) - f(title.start))}><Title /></Sequence>
      {graphics.map((g) => (
        <Sequence key={`g${g.id}`} from={f(g.start)} durationInFrames={Math.max(1, f(g.end) - f(g.start))}><Graphic g={g} /></Sequence>
      ))}
      <FxLayer fx={fx} fps={fps} shots={shots} geom={geom} brand={brand} hasCutout={cutout} faceBox={faceBox} />
      <Sequence from={f(endLogo.start)} durationInFrames={Math.max(1, f(endLogo.end) - f(endLogo.start))}><EndLogo /></Sequence>
      <AbsoluteFill><Caption /></AbsoluteFill>
    </AbsoluteFill>
  );
};
