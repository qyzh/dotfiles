-- Change the default Omarchy look'n'feel.

-- https://wiki.hypr.land/Configuring/Basics/Variables/#general
hl.config({
  general = {
    --     -- No gaps between windows or borders.
    --     gaps_in = 0,
    --     gaps_out = 0,
    --     border_size = 0,
    allow_tearing = true,
    --     -- Change to niri-like side-scrolling layout.
    --     layout = "scrolling",
  },
})

-- https://wiki.hypr.land/Configuring/Basics/Variables/#decoration
hl.config({
  decoration = {
    blur = {
      enabled = true,
      size = 8,
      passes = 3,
      brightness = 0.8,
      contrast = 0.9,
      new_optimizations = true
    },
  },
})

-- https://wiki.hypr.land/Configuring/Basics/Variables/#animations
-- hl.config({
--   animations = {
--     -- Disable all animations.
--     enabled = false,
--   },
-- })

-- https://wiki.hypr.land/Configuring/Basics/Variables/#layout
-- hl.config({
--   layout = {
--     -- Avoid overly wide single-window layouts on wide screens.
--     single_window_aspect_ratio = { 1, 1 },
--   },
-- })

-- https://wiki.hypr.land/Configuring/Layouts/Scrolling-Layout/
-- hl.config({
--   scrolling = {
--     -- See only one column per screen instead of two.
--     column_width = 0.97,
--   },
-- })
--
--

-- hl.window_rule({
--   match = { class = "steam" },
--   workspace = "8 silent"
-- })
-- hl.window_rule({
--   match = { class = "dota2" },
--   immediate = true,
-- })
-- hl.window_rule({
--   match = { class = "Spotify" },
--   workspace = "5"
-- })
--
-- hl.layer_rule({
--   match = { namespace = "omarchy-spotlight" },
--   blur = true,
--   ignore_alpha = 0.4,
-- })
-- hl.window_rule({
--   match = { class = "vesktop", "chrome-discord.com__channels_@me-Default" },
--   workspace = "5 silent"
-- })
