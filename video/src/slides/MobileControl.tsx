import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, wipeRight, stagger } from "../animations";

const telegramItems = [
  "/source add \u2014 track a new feed",
  "/digest run \u2014 trigger on demand",
  "/status \u2014 check health at a glance",
  "/source wizard \u2014 guided setup",
];

const webItems = [
  "Full profile and source management",
  "Run center with live progress",
  "Timeline view of every digest",
  "Onboarding wizard with source packs",
];

interface ColumnProps {
  title: string;
  items: string[];
  frame: number;
  baseDelay: number;
}

const Column: React.FC<ColumnProps> = ({ title, items, frame, baseDelay }) => (
  <div
    style={{
      flex: 1,
      backgroundColor: colors.surface,
      padding: 48,
      display: "flex",
      flexDirection: "column",
      gap: 24,
      ...fadeUpStyle(frame, baseDelay),
    }}
  >
    <p
      style={{
        fontFamily: fonts.heading,
        fontSize: 42,
        color: colors.textPrimary,
        letterSpacing: 2,
        margin: 0,
      }}
    >
      {title}
    </p>
    <div
      style={{
        width: 60 * wipeRight(frame, baseDelay + 8, 12),
        height: 3,
        backgroundColor: colors.gold,
      }}
    />
    {items.map((item, i) => (
      <p
        key={i}
        style={{
          fontFamily: fonts.body,
          fontSize: 30,
          color: colors.textSecondary,
          fontStyle: "italic",
          lineHeight: 1.7,
          margin: 0,
          opacity: fadeIn(frame, stagger(i, baseDelay + 12, 8)),
        }}
      >
        {item}
      </p>
    ))}
  </div>
);

export const MobileControl: React.FC = () => {
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
            MANAGE FROM ANYWHERE
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
            No SSH required
          </h2>
        </div>

        <div style={{ display: "flex", gap: 60, flex: 1 }}>
          <Column
            title="TELEGRAM BOT"
            items={telegramItems}
            frame={frame}
            baseDelay={15}
          />
          <Column
            title="WEB CONSOLE"
            items={webItems}
            frame={frame}
            baseDelay={25}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
