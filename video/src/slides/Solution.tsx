import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, wipeRight } from "../animations";

export const Solution: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 32,
          padding: "0 200px",
          textAlign: "center",
        }}
      >
        <p
          style={{
            fontFamily: fonts.heading,
            fontSize: 28,
            color: colors.gold,
            letterSpacing: 6,
            margin: 0,
            opacity: fadeIn(frame, 0),
          }}
        >
          THE SOLUTION
        </p>

        <h2
          style={{
            fontFamily: fonts.heading,
            fontSize: 100,
            color: colors.textPrimary,
            letterSpacing: 1,
            lineHeight: 1.1,
            margin: 0,
            ...fadeUpStyle(frame, 8),
          }}
        >
          One brief. Every source.
        </h2>

        <div
          style={{
            width: 80 * wipeRight(frame, 22, 15),
            height: 4,
            backgroundColor: colors.gold,
          }}
        />

        <p
          style={{
            fontFamily: fonts.body,
            fontSize: 36,
            color: colors.textSecondary,
            fontStyle: "italic",
            lineHeight: 1.5,
            margin: 0,
            maxWidth: 1200,
            ...fadeUpStyle(frame, 28),
          }}
        >
          RSS, YouTube, GitHub, and X — deduplicated, scored, and ranked into a
          daily brief delivered to Telegram and Obsidian.
        </p>
      </div>
    </AbsoluteFill>
  );
};
