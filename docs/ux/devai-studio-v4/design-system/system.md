# Authoritative design system

Only tokens.json/tokens.css govern new visuals. Prior board hex values are superseded. Contrast measurements are in contrast.csv using WCAG relative luminance. Sage, peach and border are decorative; use primary text on peach/sage backgrounds. The pale border is not adequate as the sole input or focus boundary: controlBorder is required. Error/warning use dark semantic text on surface; no white text on arbitrary sage/peach buttons.

| Token | Value |
|---|---|
| background | #F2EDE5 |
| surface | #FAF7F2 |
| secondarySurface | #E8E0D5 |
| forest | #173D32 |
| forestHover | #245646 |
| sage | #6E9F83 |
| peach | #E7B095 |
| text | #20352D |
| muted | #615E57 |
| border | #CFC6BA |
| controlBorder | #82786B |
| error | #B42332 |
| warning | #966000 |
| onForest | #FAF7F2 |
| successSurface | #E2EBE1 |
| errorSurface | #F6E1DE |
| warningSurface | #F3E6CE |
| focus | #245646 |

Typography: web UI Inter/system, body 16/24, labels/captions 14/20; primary editorial headline Georgia 32/40 or 40/48, restrained to heading/hero. iOS native SF text styles, body 17 and caption 15; all Dynamic Type categories supported. Tab labels follow native system style, not arbitrary tiny captions. Long titles wrap; never truncate important review copy. At accessibility text sizes decorative serif switches to system if required for reflow.

Spacing: 4/8/12/16/24/32/48/64. Web 12-column grid, max 1280 content, 24 gutter, 32 outer desktop padding; 16 narrow/mobile. Content hierarchy uses whitespace and dividing rules rather than card around every row. Primary surfaces remain warm. One primary action per local task. Forest sidebar 232 wide, selected row subtle light forest plus leading marker; no purple. Control radius 12, panels 18, feature groups 20, sheets 24. Floating overlays shadow 0 12px 40px rgba(32,53,45,.12); flat lists no shadow. Icons: bundled outline symbols 20–24 web, equivalent SF Symbols native, named semantic mapping; brand mark abstract four-point leaf/star retained as wordmark accent, never a navigational icon.

Buttons 48px web/native with 44px/pt minimum icon hit targets; label 16 or native headline, 16 horizontal padding. Inputs 52px/52pt min grow for large type; visible label, placeholder only example. Hover forestHover, pressed forest with 2px inset, focus 2px focus ring +2px surface gap. Disabled control uses secondary surface/muted text and explicit nearby reason, not opacity alone. Loading preserves label and width. Semantic success = forest + check, warning = warning + triangle, failure = error + exclamation; no color-only state.

Media: contain-fit full 4:5/9:16 art; never crop content in editor/review. Thumbnail cover-fit permitted with accessible complete-preview entry. No mock preview masquerades as real generated media; fixture title “Source-grounded AI workflow” is explicitly sample design data. Editorial imagery may be freeform model art, but app shell/token structure remains deterministic.

Motion: 120ms micro, 180ms panel; reduced motion disables shimmer, sliding progress simulation and celebratory effects. Haptic once for meaningful accepted action/error, none per polling tick. No autoplay video/music. Dark theme is outside initial visual scope; respect system contrast/reduced-transparency settings without inventing an incomplete second palette.
