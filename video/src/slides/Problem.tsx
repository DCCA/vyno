import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, wipeRight } from "../animations";

export const Problem: React.FC = () => {
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
          gap: 20,
          padding: "0 160px",
          textAlign: "center",
        }}
      >
        <p
          style={{
            fontFamily: fonts.heading,
            fontSize: 80,
            color: colors.textPrimary,
            letterSpacing: 1,
            margin: 0,
            ...fadeUpStyle(frame, 5),
          }}
        >
          YOU FOLLOW 100+ AI SOURCES
        </p>

        <p
          style={{
            fontFamily: fonts.heading,
            fontSize: 80,
            color: colors.gold,
            letterSpacing: 1,
            margin: 0,
            ...fadeUpStyle(frame, 20),
          }}
        >
          YOU READ MAYBE 10.
        </p>

        {/* Divider */}
        <div
          style={{
            width: 80 * wipeRight(frame, 35, 15),
            height: 2,
            backgroundColor: colors.surfaceMuted,
          }}
        />

        <p
          style={{
            fontFamily: fonts.body,
            fontSize: 48,
            color: colors.textMuted,
            fontStyle: "italic",
            margin: 0,
            opacity: fadeIn(frame, 40),
          }}
        >
          The rest is noise.
        </p>
      </div>
    </AbsoluteFill>
  );
};
