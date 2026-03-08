# Design

## Approach
- Store all new source additions in `data/sources.local.yaml`, which is the repo's mutable overlay path for operator-local source changes.
- Keep `config/sources.yaml` untouched so tracked defaults remain stable.
- Add only validated RSS feed URLs.
- Add only YouTube creators whose public channel IDs could be resolved reliably from the current YouTube page payload.
- Exclude `youtube_query` additions from this change because the public YouTube search feed endpoint returned `400` for the tested agent-topic queries on March 8, 2026.

## Added Sources
- RSS:
  - Hugging Face blog
  - LangChain blog
  - Simon Willison atom feed
  - Latent Space
  - Interconnects
  - Sebastian Raschka
  - Understanding AI
  - Lilian Weng
  - Replicate blog
- YouTube channels:
  - AI Jason
  - Cole Medin
  - NetworkChuck

## Verification
- Load the effective merged sources via the existing config/overlay loader.
- Confirm no canonical duplicates exist in the merged RSS, YouTube channel, or YouTube query sets.
- Check the newly added public RSS endpoints and YouTube feed URLs over HTTP.
