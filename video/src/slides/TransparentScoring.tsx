import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, stagger } from "../animations";

const axes = [
  {
    range: "0\u201360",
    label: "RELEVANCE",
    desc: "How closely does this match your topics, entities, and interests?",
  },
  {
    range: "0\u201330",
    label: "QUALITY",
    desc: "Depth, originality, and technical substance of the content.",
  },
  {
    range: "0\u201310",
    label: "NOVELTY",
    desc: "Is this genuinely new, or a rehash of yesterday\u2019s story?",
  },
];

export const TransparentScoring: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 48,
          padding: "100px 120px",
          height: "100%",
          boxSizing: "border-box",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
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
            FULL TRANSPARENCY
          </p>
          <h2
            style={{
              fontFamily: fonts.heading,
              fontSize: 80,
              color: colors.textPrimary,
              letterSpacing: 1,
              margin: 0,
              ...fadeUpStyle(frame, 5),
            }}
          >
            Every score. Every reason.
          </h2>
        </div>

        <div style={{ display: "flex", gap: 40 }}>
          {axes.map((axis, i) => {
            const delay = stagger(i, 15, 12);
            return (
              <div
                key={axis.label}
                style={{
                  flex: 1,
                  backgroundColor: colors.surface,
                  padding: 40,
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                  ...fadeUpStyle(frame, delay),
                }}
              >
                <p
                  style={{
                    fontFamily: fonts.heading,
                    fontSize: 80,
                    color: colors.gold,
                    letterSpacing: 1,
                    margin: 0,
                  }}
                >
                  {axis.range}
                </p>
                <p
                  style={{
                    fontFamily: fonts.heading,
                    fontSize: 36,
                    color: colors.textPrimary,
                    letterSpacing: 2,
                    margin: 0,
                  }}
                >
                  {axis.label}
                </p>
                <p
                  style={{
                    fontFamily: fonts.body,
                    fontSize: 28,
                    color: colors.textSecondary,
                    fontStyle: "italic",
                    lineHeight: 1.5,
                    margin: 0,
                  }}
                >
                  {axis.desc}
                </p>
              </div>
            );
          })}
        </div>

        <p
          style={{
            fontFamily: fonts.heading,
            fontSize: 28,
            color: colors.textMuted,
            letterSpacing: 2,
            textAlign: "center",
            margin: 0,
            opacity: fadeIn(frame, 50),
          }}
        >
          60+ PROFILE SETTINGS &middot; FEEDBACK WITH 14-DAY HALF-LIFE DECAY
          &middot; CONFIG HISTORY + ROLLBACK
        </p>
      </div>
    </AbsoluteFill>
  );
};
