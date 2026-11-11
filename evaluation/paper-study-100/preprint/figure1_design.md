# Figure 1 design record

The reviewed conceptual diagram replaces the original six-box snake layout. Content is grouped into human guidance, four research stages, persistent evidence, and public projection. No empirical measurements are represented by this schematic. AI-assisted visual design is disclosed in the manuscript. The original generated image is retained unchanged in figures/fig1_workflow.png; build_figure1.py embeds it in the PDF.

The earlier source and derivation stages are combined as Read & formalize; implementation and computation remain distinct; assessment and its revision loop are made explicit. All artifact categories from the original diagram remain visible.

## Design specification

Create a publication-quality Figure 1 for a scholarly arXiv technical report. Create a crisp, precise, high-resolution, flat vector-style scientific systems schematic on PURE WHITE. Wide landscape 3:2 ratio. Sharp dark typography, ample white space, delicate 1px rules, restrained navy blue and teal accents, pale blue-gray section fields. No gradients, no 3D, no shadows, no decorative brains, no robots, no stock art, no massive overall heading. This is a conceptual workflow, NOT empirical evidence. Preserve the scientific meaning but completely replace the amateur six-box snake diagram.

The visual must be understandable at 165mm paper width. Use fewer words, large clear type, exact English text. Main reading direction is left-to-right. 3 horizontal levels with a bottom artifact row:
TOP: a thin airy governance rail across almost full width, navy label "Human guidance" at left. Three short aligned labels along the rail: "Scope & assumptions", "Modeling choices", "Scientific interpretation". Dashed downward connections to the main workflow show guidance, not fully autonomous operation.
MIDDLE HERO: four well-spaced stages inside a subtle very pale blue frame whose small top-left label is "PRAgent". Four precise small stages with elegant simple line icons (a paper, equation brackets, code brackets, checkmark chart); titles must be short:
1 "Read & formalize" with smaller subtitle "Source objects · equations"
2 "Implement" with smaller subtitle "Models · parameters · code"
3 "Compute & check" with smaller subtitle "Arrays · physical diagnostics"
4 "Assess" with smaller subtitle "Comparisons · limits"
Join these FOUR stages with clean short horizontal arrows. Icons should be tiny supporting signals, not big illustrations. Put one thin teal return arrow below the main stages labeled "Revise when needed", running from stage 4 back to stage 2, without crossing any text.
BOTTOM: a structured full-width information layer with two distinct grouped areas linked by one rightward arrow:
LEFT about 62% width, label "Versioned research case". Below it, FOUR small compact file-like pills with tasteful mini glyphs and exactly these labels: "Derivations", "Code & config", "Data & figures", "Checks & review".
RIGHT about 30% width, teal-tinted group label "RunThePaper". Subtitle "Public research artifacts". Below three small plain words separated by centered dots: "Inspect · reuse · extend".
A single subtle downward arrow from the central workflow to the LEFT case layer is labeled "Persist evidence". An arrow from LEFT case layer to RIGHT RunThePaper is labeled "Public projection" and must remain readable.
At bottom-right in tiny but readable gray type add exactly: "Workflow schematic; completion varies by case."
Do not add title Figure 1; the manuscript caption will provide it. All text must be spelled exactly and placed inside generous bounding regions without overlap. One consistent professional sans-serif font. Use numbered stages 01, 02, 03, 04 as small teal eyebrow labels. Prioritize hierarchy and architectural relationships over a grid of big boxes.
