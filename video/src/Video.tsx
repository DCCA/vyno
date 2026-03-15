import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { interpolate } from "remotion";
import { colors, SLIDE_DURATIONS } from "./theme";

import { Cover } from "./slides/Cover";
import { Problem } from "./slides/Problem";
import { Solution } from "./slides/Solution";
import { HowItWorks } from "./slides/HowItWorks";
import { TransparentScoring } from "./slides/TransparentScoring";
import { SelfHosted } from "./slides/SelfHosted";
import { MobileControl } from "./slides/MobileControl";
import { KnowledgeArchive } from "./slides/KnowledgeArchive";
import { Differentiators } from "./slides/Differentiators";
import { Closing } from "./slides/Closing";

const FADE = 10; // frames for cross-fade between slides

const slides = [
  { component: Cover, duration: SLIDE_DURATIONS.cover },
  { component: Problem, duration: SLIDE_DURATIONS.problem },
  { component: Solution, duration: SLIDE_DURATIONS.solution },
  { component: HowItWorks, duration: SLIDE_DURATIONS.howItWorks },
  { component: TransparentScoring, duration: SLIDE_DURATIONS.scoring },
  { component: SelfHosted, duration: SLIDE_DURATIONS.selfHosted },
  { component: MobileControl, duration: SLIDE_DURATIONS.mobileControl },
  { component: KnowledgeArchive, duration: SLIDE_DURATIONS.archive },
  { component: Differentiators, duration: SLIDE_DURATIONS.differentiators },
  { component: Closing, duration: SLIDE_DURATIONS.closing },
];

export const MarketingVideo: React.FC = () => {
  const frame = useCurrentFrame();

  let offset = 0;
  const sequences = slides.map((slide, i) => {
    const from = offset;
    offset += slide.duration;
    const Component = slide.component;

    // Fade out at end of each slide (except the last)
    const isLast = i === slides.length - 1;
    const slideEnd = from + slide.duration;
    const fadeOutOpacity = isLast
      ? 1
      : interpolate(
          frame,
          [slideEnd - FADE, slideEnd],
          [1, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

    // Fade in at start of each slide (except the first)
    const isFirst = i === 0;
    const fadeInOpacity = isFirst
      ? 1
      : interpolate(
          frame,
          [from, from + FADE],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
        );

    return (
      <Sequence key={i} from={from} durationInFrames={slide.duration}>
        <AbsoluteFill style={{ opacity: Math.min(fadeInOpacity, fadeOutOpacity) }}>
          <Component />
        </AbsoluteFill>
      </Sequence>
    );
  });

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      {sequences}
    </AbsoluteFill>
  );
};
