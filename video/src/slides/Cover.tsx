import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, wipeRight } from "../animations";

export const Cover: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      {/* Gold accent bar */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 8,
          height: `${wipeRight(frame, 0, 30) * 100}%`,
          backgroundColor: colors.gold,
        }}
      />

      {/* Content */}
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 320,
          display: "flex",
          flexDirection: "column",
          gap: 28,
        }}
      >
        <h1
          style={{
            fontFamily: fonts.heading,
            fontSize: 140,
            color: colors.textPrimary,
            letterSpacing: 2,
            lineHeight: 0.9,
            margin: 0,
            ...fadeUpStyle(frame, 10),
          }}
        >
          AI DAILY DIGEST
        </h1>

        {/* Gold divider */}
        <div
          style={{
            width: 120 * wipeRight(frame, 25, 20),
            height: 4,
            backgroundColor: colors.gold,
          }}
        />

        <p
          style={{
            fontFamily: fonts.body,
            fontSize: 48,
            color: colors.textSecondary,
            fontStyle: "italic",
            margin: 0,
            ...fadeUpStyle(frame, 30),
          }}
        >
          Your AI news, your rules, your machine.
        </p>

        <p
          style={{
            fontFamily: fonts.heading,
            fontSize: 28,
            color: colors.textMuted,
            letterSpacing: 6,
            margin: 0,
            opacity: fadeIn(frame, 45),
          }}
        >
          MARCH 2026
        </p>
      </div>
    </AbsoluteFill>
  );
};
