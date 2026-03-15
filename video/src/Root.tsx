import { Composition } from "remotion";
import { MarketingVideo } from "./Video";
import { TOTAL_FRAMES, FPS } from "./theme";
import { loadFont } from "@remotion/google-fonts/BebasNeue";
import { loadFont as loadCormorant } from "@remotion/google-fonts/CormorantGaramond";

loadFont();
loadCormorant();

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MarketingVideo"
        component={MarketingVideo}
        durationInFrames={TOTAL_FRAMES}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
