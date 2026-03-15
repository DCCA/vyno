import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, stagger } from "../animations";

const cards = [
  {
    title: "VS NEWSLETTERS",
    desc: "One-size-fits-all. No source control, no tuning, no data ownership.",
  },
  {
    title: "VS RSS READERS",
    desc: "Show everything, prioritize nothing. No scoring, no dedup, no brief.",
  },
  {
    title: "VS ZAPIER + GPT",
    desc: "Weeks of plumbing, per-zap fees, fragile multi-step automations.",
  },
  {
    title: "VS SOCIAL ALGORITHMS",
    desc: "Optimized for engagement, not your needs. Opaque, non-portable, no archive.",
  },
];

export const Differentiators: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 40,
          padding: "80px 120px",
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
            WHY NOT SOMETHING ELSE?
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
            Purpose-built beats duct tape
          </h2>
        </div>

        {/* 2x2 grid */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 32,
            flex: 1,
          }}
        >
          {[0, 1].map((row) => (
            <div key={row} style={{ display: "flex", gap: 32, flex: 1 }}>
              {cards.slice(row * 2, row * 2 + 2).map((card, i) => {
                const idx = row * 2 + i;
                const delay = stagger(idx, 15, 10);
                return (
                  <div
                    key={card.title}
                    style={{
                      flex: 1,
                      backgroundColor: colors.surface,
                      padding: 32,
                      display: "flex",
                      flexDirection: "column",
                      gap: 12,
                      ...fadeUpStyle(frame, delay),
                    }}
                  >
                    <p
                      style={{
                        fontFamily: fonts.heading,
                        fontSize: 32,
                        color: colors.gold,
                        letterSpacing: 2,
                        margin: 0,
                      }}
                    >
                      {card.title}
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
                      {card.desc}
                    </p>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
