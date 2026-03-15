import { AbsoluteFill, useCurrentFrame } from "remotion";
import { colors, fonts } from "../theme";
import { fadeIn, fadeUpStyle, stagger } from "../animations";

const frontmatterLines = [
  { text: "---", color: colors.textMuted },
  { text: "date: 2026-03-15", color: colors.gold },
  { text: "run_id: d7f3a91b", color: colors.textSecondary },
  { text: "tags: [ai, digest]", color: colors.textSecondary },
  { text: "---", color: colors.textMuted },
  { text: "", color: "transparent" },
  { text: "# AI DAILY DIGEST", color: colors.textPrimary, heading: true },
  { text: "## Must-Read", color: colors.gold, heading: true },
  {
    text: "GPT-5 architecture details leak...",
    color: colors.textSecondary,
  },
];

export const KnowledgeArchive: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: colors.bg }}>
      <div
        style={{
          display: "flex",
          gap: 80,
          padding: "100px 120px",
          height: "100%",
          boxSizing: "border-box",
          alignItems: "center",
        }}
      >
        {/* Left: text */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: 32,
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
            KNOWLEDGE ARCHIVE
          </p>
          <h2
            style={{
              fontFamily: fonts.heading,
              fontSize: 64,
              color: colors.textPrimary,
              letterSpacing: 1,
              lineHeight: 1.1,
              margin: 0,
              ...fadeUpStyle(frame, 5),
            }}
          >
            Every digest saved. Every insight findable.
          </h2>
          <p
            style={{
              fontFamily: fonts.body,
              fontSize: 30,
              color: colors.textSecondary,
              fontStyle: "italic",
              lineHeight: 1.5,
              margin: 0,
              ...fadeUpStyle(frame, 15),
            }}
          >
            Obsidian markdown with YAML frontmatter — date, tags, run ID.
            Timeline view in the web console. Full artifact archiving. Search,
            link, and build on months of AI developments.
          </p>
        </div>

        {/* Right: mock Obsidian note */}
        <div
          style={{
            flex: 1,
            backgroundColor: colors.surface,
            padding: 32,
            display: "flex",
            flexDirection: "column",
            gap: 8,
            ...fadeUpStyle(frame, 20),
          }}
        >
          {frontmatterLines.map((line, i) => (
            <p
              key={i}
              style={{
                fontFamily: line.heading ? fonts.heading : fonts.body,
                fontSize: line.heading ? 36 : 28,
                color: line.color,
                letterSpacing: line.heading ? 1 : 0,
                lineHeight: 1.5,
                margin: 0,
                minHeight: line.text === "" ? 12 : undefined,
                opacity: fadeIn(frame, stagger(i, 25, 5)),
              }}
            >
              {line.text}
            </p>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
