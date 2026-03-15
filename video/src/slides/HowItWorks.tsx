import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, wipeRight, stagger } from "../animations";

const steps = [
  {
    num: "01",
    title: "CONNECT YOUR SOURCES",
    desc: "Add RSS feeds, YouTube channels, GitHub repos, and X accounts. Start with a curated source pack or bring your own.",
  },
  {
    num: "02",
    title: "LET THE PIPELINE RUN",
    desc: "On your schedule, the engine fetches, deduplicates, and scores every item against your profile — topics, entities, quality signals.",
  },
  {
    num: "03",
    title: "READ YOUR BRIEF",
    desc: "A ranked digest lands in Telegram and Obsidian. Must-reads at the top. Every item shows its score. Every run is archived.",
  },
];

export const HowItWorks: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 60,
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
            HOW IT WORKS
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
            Three steps to signal
          </h2>
        </div>

        <div
          style={{
            display: "flex",
            gap: 60,
            flex: 1,
          }}
        >
          {steps.map((step, i) => {
            const delay = stagger(i, 15, 15);
            return (
              <div
                key={step.num}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  gap: 16,
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
                  {step.num}
                </p>
                {/* Gold line under number */}
                <div
                  style={{
                    width: 40 * wipeRight(frame, delay + 10, 12),
                    height: 3,
                    backgroundColor: colors.gold,
                  }}
                />
                <p
                  style={{
                    fontFamily: fonts.heading,
                    fontSize: 36,
                    color: colors.textPrimary,
                    letterSpacing: 1,
                    margin: 0,
                  }}
                >
                  {step.title}
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
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};
