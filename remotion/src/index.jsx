import React from 'react';
import {registerRoot, Composition} from 'remotion';
import {Edit} from './Edit';
import data from './props.json';

const Root = () => (
  <Composition
    id="Edit"
    component={Edit}
    durationInFrames={Math.round(data.duration * data.fps)}
    fps={data.fps}
    width={1080}
    height={1920}
  />
);

registerRoot(Root);
