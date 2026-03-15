import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, wipeRight } from "../animations";

export const Closing: React.FC = () => {
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
        <h2
          style={{
            fontFamily: fonts.heading,
            fontSize: 120,
            color: colors.textPrimary,
            letterSpacing: 1,
            lineHeight: 1.1,
            margin: 0,
            ...fadeUpStyle(frame, 0),
          }}
        >
          Cut through the noise.
        </h2>

        <div
          style={{
            width: 120 * wipeRight(frame, 15, 15),
            height: 4,
            backgroundColor: colors.gold,
          }}
        />

        <p
          style={{
            fontFamily: fonts.body,
            fontSize: 56,
            color: colors.gold,
            fontStyle: "italic",
            margin: 0,
            ...fadeUpStyle(frame, 20),
          }}
        >
          Keep the signal.
        </p>

        {/* CTA button */}
        <div
          style={{
            marginTop: 20,
            backgroundColor: colors.gold,
            padding: "20px 48px",
            opacity: fadeIn(frame, 35),
            transform: `scale(${0.9 + 0.1 * fadeIn(frame, 35)})`,
          }}
        >
          <p
            style={{
              fontFamily: fonts.heading,
              fontSize: 32,
              color: colors.bg,
              letterSpacing: 4,
              margin: 0,
            }}
          >
            GET STARTED
          </p>
        </div>

        <p
          style={{
            fontFamily: fonts.body,
            fontSize: 28,
            color: colors.textMuted,
            fontStyle: "italic",
            margin: 0,
            opacity: fadeIn(frame, 45),
          }}
        >
          github.com/your-org/ai-daily-digest
        </p>
      </div>
    </AbsoluteFill>
  );
};
