// Build a 6-slide PPTX from Study_proposal.md content, matching styletemplate.pptx style.
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 inches (matches template)
pres.author = "Group Z";
pres.title = "Form of Explanation - Explainability vs. Explicability under Multitasking Load";

// --- Style tokens lifted from styletemplate.pptx ---
const C = {
  bg:        "FFFFFF",
  headerBar: "D5D7DA",
  navy:      "143847", // brand navy
  ink:       "1A1A1A", // body text
  muted:     "5A6770", // secondary
  rule:      "143847", // accent rule
  panelBg:   "F4F6F8", // light panel
  panelLine: "C9D2D9",
  accent:    "8C1D2C", // subtle accent for callouts
};
const FONT = "Calibri";

const SLIDE_W = 13.333;
const SLIDE_H = 7.5;

function addChrome(slide, slideNum, totalSlides, footerLeft) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: SLIDE_W, h: 0.6,
    fill: { color: C.headerBar }, line: { color: C.headerBar },
  });
  slide.addText("UNIVERSITÄT ZU LÜBECK", {
    x: 0.45, y: 0.08, w: 7.5, h: 0.22,
    fontFace: FONT, fontSize: 10, bold: true, color: C.navy, margin: 0,
  });
  slide.addText("Human-Centered Trustworthy AI (CS5076-KP12)", {
    x: 0.45, y: 0.30, w: 7.5, h: 0.22,
    fontFace: FONT, fontSize: 10, color: C.ink, margin: 0,
  });
  slide.addText("Group Z  ·  Lilian Obidike · Sheethal Mohan Prabhu · Andrea Thelen", {
    x: 5.0, y: 0.08, w: 7.9, h: 0.22,
    fontFace: FONT, fontSize: 10, color: C.navy, align: "right", margin: 0,
  });
  slide.addText("Project pitch  ·  14 May 2026", {
    x: 5.0, y: 0.30, w: 7.9, h: 0.22,
    fontFace: FONT, fontSize: 10, color: C.ink, align: "right", margin: 0,
  });
  slide.addShape(pres.shapes.LINE, {
    x: 0.45, y: 7.10, w: SLIDE_W - 0.9, h: 0,
    line: { color: C.panelLine, width: 0.5 },
  });
  slide.addText(footerLeft, {
    x: 0.45, y: 7.15, w: 9.5, h: 0.28,
    fontFace: FONT, fontSize: 9, color: C.muted, italic: true, margin: 0,
  });
  slide.addText(`${slideNum} / ${totalSlides}`, {
    x: SLIDE_W - 1.5, y: 7.15, w: 1.05, h: 0.28,
    fontFace: FONT, fontSize: 9, color: C.muted, align: "right", margin: 0,
  });
}

function addTitle(slide, title, dek) {
  slide.addText(title, {
    x: 0.45, y: 0.85, w: SLIDE_W - 0.9, h: 0.55,
    fontFace: FONT, fontSize: 26, bold: true, color: C.navy, margin: 0,
  });
  slide.addShape(pres.shapes.LINE, {
    x: 0.45, y: 1.42, w: 1.6, h: 0,
    line: { color: C.rule, width: 1.5 },
  });
  if (dek) {
    slide.addText(dek, {
      x: 0.45, y: 1.50, w: SLIDE_W - 0.9, h: 0.34,
      fontFace: FONT, fontSize: 13, italic: true, color: C.muted, margin: 0,
    });
  }
}

const TOTAL = 6;
const FOOTER = "Form of Explanation — Explainability vs. Explicability under Multitasking Load";

// SLIDE 1 - TITLE
{
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  addChrome(slide, 1, TOTAL, FOOTER);
  slide.addText("Form of Explanation", {
    x: 0.6, y: 2.0, w: SLIDE_W - 1.2, h: 1.0,
    fontFace: FONT, fontSize: 48, bold: true, color: C.navy, margin: 0,
  });
  slide.addText("Explainability vs. Explicability under Multitasking Load", {
    x: 0.6, y: 3.0, w: SLIDE_W - 1.2, h: 0.55,
    fontFace: FONT, fontSize: 22, color: C.ink, margin: 0,
  });
  slide.addShape(pres.shapes.LINE, {
    x: 0.6, y: 3.7, w: 2.4, h: 0,
    line: { color: C.rule, width: 2 },
  });
  slide.addText(
    "Does the form of an automation aid's reasoning explanation — holding information " +
    "content constant — change whether the operator's mental model actually updates " +
    "under multitasking load?",
    {
      x: 0.6, y: 3.9, w: SLIDE_W - 1.2, h: 1.1,
      fontFace: FONT, fontSize: 16, italic: true, color: C.ink, margin: 0,
    }
  );
  slide.addText("Group Z", {
    x: 0.6, y: 5.7, w: 8, h: 0.32,
    fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
  });
  slide.addText("Lilian Obidike  ·  Sheethal Mohan Prabhu  ·  Andrea Thelen", {
    x: 0.6, y: 6.05, w: 8, h: 0.3,
    fontFace: FONT, fontSize: 13, color: C.ink, margin: 0,
  });
  slide.addText("Universität zu Lübeck  ·  Project pitch  ·  14 May 2026", {
    x: 0.6, y: 6.35, w: 9, h: 0.3,
    fontFace: FONT, fontSize: 12, italic: true, color: C.muted, margin: 0,
  });
}

// SLIDE 2 - PROBLEM & RELEVANCE
{
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  addChrome(slide, 2, TOTAL, FOOTER);
  addTitle(slide, "Problem & relevance",
    "Two systems can be equally transparent — yet only one updates the operator's mental model.");

  const colY = 2.05;
  const colH = 4.4;
  const leftX = 0.45, leftW = 6.0;
  const rightX = 6.85, rightW = 6.0;

  slide.addText("Problem / research gap", {
    x: leftX, y: colY, w: leftW, h: 0.34,
    fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "When an AI system explains itself, two things happen separately: the system produces an explanation (",
      options: { fontSize: 13 } },
    { text: "explainability", options: { fontSize: 13, italic: true } },
    { text: "), and the operator's mental model updates (",
      options: { fontSize: 13 } },
    { text: "explicability", options: { fontSize: 13, italic: true } },
    { text: ").", options: { fontSize: 13, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "The transparency literature has focused on ", options: { fontSize: 13 } },
    { text: "how much", options: { fontSize: 13, italic: true } },
    { text: " information an aid provides — not on ", options: { fontSize: 13 } },
    { text: "how", options: { fontSize: 13, italic: true } },
    { text: " it is delivered.", options: { fontSize: 13, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "We isolate the form effect by holding information content constant.",
      options: { fontSize: 13, bold: true, color: C.navy } },
  ], {
    x: leftX, y: colY + 0.40, w: leftW, h: colH - 0.4,
    fontFace: FONT, color: C.ink, paraSpaceAfter: 4, margin: 0, valign: "top",
  });

  slide.addShape(pres.shapes.LINE, {
    x: 6.65, y: colY, w: 0, h: colH,
    line: { color: C.panelLine, width: 0.75 },
  });

  slide.addText("Why it is relevant", {
    x: rightX, y: colY, w: rightW, h: 0.34,
    fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "The distinction matters wherever a human supervises an automated system — ",
      options: { fontSize: 13 } },
    { text: "aviation, medical monitoring, autonomous driving aids.",
      options: { fontSize: 13, bold: true, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "If an explanation is long and reads like a status log, the operator may feel informed without being able to predict the system's next action.",
      options: { fontSize: 13, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "That failure mode has measurable consequences for detecting automation errors — and it is precisely what the lecture warns against.",
      options: { fontSize: 13, italic: true, color: C.navy } },
  ], {
    x: rightX, y: colY + 0.40, w: rightW, h: colH - 0.4,
    fontFace: FONT, color: C.ink, paraSpaceAfter: 4, margin: 0, valign: "top",
  });
}

// SLIDE 3 - CONCEPT: THREE FORMS
{
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  addChrome(slide, 3, TOTAL, FOOTER);
  addTitle(slide, "Concept — three forms of explanation",
    "All three forms communicate the aid's reasoning. Information content is matched; only the form varies.");

  const cardY = 2.10;
  const cardH = 4.50;
  const gap = 0.20;
  const cardW = (SLIDE_W - 0.9 - 2 * gap) / 3;
  const startX = 0.45;

  const cards = [
    {
      tag: "F1",
      title: "Verbose / always-on",
      summary: "Routine status prose, every cycle.",
      example: "\"Scale-1 was 47.0 > upper bound 45.0, auto-aid not engaged. Scale-2: 31.5, in range...\"",
      note: "Embeds every fact in routine prose — fires on every automation cycle.",
    },
    {
      tag: "F2",
      title: "Selective + contrastive",
      summary: "Panel only on near-miss / miss.",
      example: "\"Reset scale-1 — would have failed in ~2.5 s.\"\n\"Skipped scale-2 — auto-aid did not act.\"",
      note: "Same facts as F1, reframed selectively and contrastively.",
    },
    {
      tag: "F3",
      title: "Selective + contrastive + actionable",
      summary: "F2 plus an explicit operator cue on misses.",
      example: "\"Skipped scale-2 — auto-aid did not act.\"\n\"Check it yourself.\"",
      note: "F3 minus F2 = the actionable cue, isolated.",
    },
  ];

  cards.forEach((c, i) => {
    const x = startX + i * (cardW + gap);
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: cardH,
      fill: { color: C.panelBg }, line: { color: C.panelLine, width: 0.75 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: 0.10,
      fill: { color: C.navy }, line: { color: C.navy },
    });
    slide.addText(c.tag, {
      x: x + 0.20, y: cardY + 0.20, w: 1.4, h: 0.45,
      fontFace: FONT, fontSize: 22, bold: true, color: C.navy, margin: 0,
    });
    slide.addText(c.title, {
      x: x + 0.20, y: cardY + 0.65, w: cardW - 0.40, h: 0.50,
      fontFace: FONT, fontSize: 14, bold: true, color: C.ink, margin: 0,
    });
    slide.addText(c.summary, {
      x: x + 0.20, y: cardY + 1.15, w: cardW - 0.40, h: 0.40,
      fontFace: FONT, fontSize: 11, italic: true, color: C.muted, margin: 0,
    });
    slide.addText("Example panel text", {
      x: x + 0.20, y: cardY + 1.65, w: cardW - 0.40, h: 0.28,
      fontFace: FONT, fontSize: 10, bold: true, color: C.navy, margin: 0,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + 0.20, y: cardY + 1.95, w: cardW - 0.40, h: 1.55,
      fill: { color: "FFFFFF" }, line: { color: C.panelLine, width: 0.5 },
    });
    slide.addText(c.example, {
      x: x + 0.30, y: cardY + 2.05, w: cardW - 0.60, h: 1.40,
      fontFace: "Consolas", fontSize: 10, color: C.ink, margin: 0,
      paraSpaceAfter: 3, valign: "top",
    });
    slide.addText(c.note, {
      x: x + 0.20, y: cardY + 3.60, w: cardW - 0.40, h: 0.80,
      fontFace: FONT, fontSize: 11, italic: true, color: C.muted, margin: 0, valign: "top",
    });
  });
}

// SLIDE 4 - HYPOTHESES
{
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  addChrome(slide, 4, TOTAL, FOOTER);
  addTitle(slide, "Research question & hypotheses",
    "Holding information content constant, does the form of a reasoning explanation produce explicability?");

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 2.05, w: SLIDE_W - 0.9, h: 0.95,
    fill: { color: C.panelBg }, line: { color: C.panelLine, width: 0.75 },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 2.05, w: 0.10, h: 0.95,
    fill: { color: C.navy }, line: { color: C.navy },
  });
  slide.addText("Research question", {
    x: 0.70, y: 2.10, w: SLIDE_W - 1.15, h: 0.30,
    fontFace: FONT, fontSize: 12, bold: true, color: C.navy, margin: 0,
  });
  slide.addText(
    "In a multitasking supervisory-control environment with an imperfect automation aid that " +
    "communicates its reasoning, does the form of the explanation — varied along Miller's criteria " +
    "of selectivity, contrastiveness and actionability — produce measurable mental-model alignment " +
    "and improved detection of automation errors, beyond what an equally informative but verbose " +
    "always-on explanation provides?",
    { x: 0.70, y: 2.40, w: SLIDE_W - 1.15, h: 0.60,
      fontFace: FONT, fontSize: 11, color: C.ink, margin: 0, valign: "top" }
  );

  slide.addText("Hypotheses  ·  H1 and H2 are the load-bearing pair", {
    x: 0.45, y: 3.15, w: SLIDE_W - 0.9, h: 0.30,
    fontFace: FONT, fontSize: 12, bold: true, color: C.navy, margin: 0,
  });

  const hY = 3.50;
  const hH = 1.70;
  const hGap = 0.20;
  const hW = (SLIDE_W - 0.9 - hGap) / 2;

  const hyps = [
    {
      tag: "H1",
      head: "Perceived informativeness vs. actual understanding (headline)",
      body: "Subjective transparency highest under F1; objective mental-model accuracy highest under F2/F3. The crossover operationalises explainability ≠ explicability.",
      load: true,
    },
    {
      tag: "H2",
      head: "Form modulates explicability",
      body: "Post-block mental-model accuracy higher under F2/F3 than F1 — even with information content matched. Selectivity + contrastive framing make the relevant facts easier to extract under load.",
      load: true,
    },
    {
      tag: "H3",
      head: "Selectivity directs attention to anomalies",
      body: "Detection rate of automation-missed events higher under F2/F3 than F1 — even though F1 announces those events too (embedded in routine status prose).",
      load: false,
    },
    {
      tag: "H4",
      head: "Saved attention is redeployed",
      body: "Performance on the non-automated tasks (communications, scheduling) higher under F2/F3 than F1 — reading less in the panel frees capacity for tasks the aid does not support.",
      load: false,
    },
  ];

  hyps.forEach((h, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.45 + col * (hW + hGap);
    const y = hY + row * (hH + 0.10);
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: hW, h: hH,
      fill: { color: "FFFFFF" }, line: { color: C.panelLine, width: 0.75 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: hH,
      fill: { color: h.load ? C.accent : C.navy },
      line: { color: h.load ? C.accent : C.navy },
    });
    slide.addText([
      { text: `${h.tag}  `, options: { bold: true, color: h.load ? C.accent : C.navy, fontSize: 13 } },
      { text: h.head, options: { bold: true, color: C.ink, fontSize: 12 } },
    ], {
      x: x + 0.20, y: y + 0.10, w: hW - 0.30, h: 0.55,
      fontFace: FONT, margin: 0, valign: "top",
    });
    slide.addText(h.body, {
      x: x + 0.20, y: y + 0.55, w: hW - 0.30, h: hH - 0.65,
      fontFace: FONT, fontSize: 11, color: C.ink, margin: 0, valign: "top",
    });
  });
}

// SLIDE 5 - METHOD
{
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  addChrome(slide, 5, TOTAL, FOOTER);
  addTitle(slide, "Method",
    "Within-subjects on the OpenMATB platform · ~20 min per participant.");

  const colY = 2.10;
  const colH = 4.55;
  const leftX = 0.45, leftW = 6.0;
  const rightX = 6.85, rightW = 6.0;

  slide.addText("Design & session", {
    x: leftX, y: colY, w: leftW, h: 0.32,
    fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
  });
  slide.addText([
    { text: "Platform.  ", options: { bold: true } },
    { text: "OpenMATB — four concurrent supervisory tasks: system monitoring, communications, scheduling, resource management.", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Automation aid.  ", options: { bold: true } },
    { text: "Runs only on system monitoring at ~78% reliability; the other three tasks compete for attention.", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Within-subjects design.  ", options: { bold: true } },
    { text: "Each participant runs all three forms (F1/F2/F3), once each on three different gauge sets — so the post-block memory probe cannot be answered by recall from another block.", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Session.  ", options: { bold: true } },
    { text: "≈20 min per participant: 3 min practice → three 5 min experimental blocks → final questionnaire battery.", options: { breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "Content matching.  ", options: { bold: true, color: C.accent } },
    { text: "F1's verbose stream contains every fact F2/F3 surface — the central design constraint. Any leak invalidates the comparison.",
      options: { italic: true } },
  ], {
    x: leftX, y: colY + 0.38, w: leftW, h: colH - 0.4,
    fontFace: FONT, fontSize: 12, color: C.ink, paraSpaceAfter: 3, margin: 0, valign: "top",
  });

  slide.addShape(pres.shapes.LINE, {
    x: 6.65, y: colY, w: 0, h: colH,
    line: { color: C.panelLine, width: 0.75 },
  });

  slide.addText("What we measure", {
    x: rightX, y: colY, w: rightW, h: 0.32,
    fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0,
  });
  slide.addText("Two kinds of measures: things the participant tells us (questionnaires) and things the platform records (key presses, response times, hits and misses). Each maps onto one or more hypotheses — detailed on the next slide.", {
    x: rightX, y: colY + 0.38, w: rightW, h: 1.0,
    fontFace: FONT, fontSize: 12, italic: true, color: C.ink, margin: 0, valign: "top",
  });

  const stripY = colY + 1.55;
  const steps = ["Practice", "Block 1", "Block 2", "Block 3", "Debrief"];
  const stepW = (rightW - 0.20) / steps.length;
  steps.forEach((s, i) => {
    const x = rightX + i * stepW + (i > 0 ? 0.05 : 0);
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: stripY, w: stepW - 0.05, h: 0.55,
      fill: { color: i === 0 || i === 4 ? C.panelBg : C.navy },
      line: { color: C.panelLine, width: 0.5 },
    });
    slide.addText(s, {
      x, y: stripY + 0.05, w: stepW - 0.05, h: 0.45,
      fontFace: FONT, fontSize: 11, bold: true,
      color: i === 0 || i === 4 ? C.navy : "FFFFFF", align: "center", margin: 0,
    });
  });
  slide.addText("3 min        →        5 min        →        5 min        →        5 min        →        questionnaires", {
    x: rightX, y: stripY + 0.65, w: rightW, h: 0.25,
    fontFace: FONT, fontSize: 9, italic: true, color: C.muted, align: "center", margin: 0,
  });

  const statY = stripY + 1.10;
  const stats = [
    { n: "4", l: "concurrent tasks" },
    { n: "78%", l: "aid reliability" },
    { n: "3 × 5", l: "min blocks" },
  ];
  const statW = (rightW - 0.30) / stats.length;
  stats.forEach((s, i) => {
    const x = rightX + i * (statW + 0.15);
    slide.addText(s.n, {
      x, y: statY, w: statW, h: 0.55,
      fontFace: FONT, fontSize: 28, bold: true, color: C.navy, align: "center", margin: 0,
    });
    slide.addText(s.l, {
      x, y: statY + 0.55, w: statW, h: 0.30,
      fontFace: FONT, fontSize: 10, color: C.muted, align: "center", italic: true, margin: 0,
    });
  });
}

// SLIDE 6 - MEASURES & CONSIDERATIONS
{
  const slide = pres.addSlide();
  slide.background = { color: C.bg };
  addChrome(slide, 6, TOTAL, FOOTER);
  addTitle(slide, "Measures & considerations",
    "Each measure maps onto a specific hypothesis; design constraints define the limits of inference.");

  const mY = 2.05;
  const mH = 1.55;
  const mGap = 0.20;
  const mW = (SLIDE_W - 0.9 - mGap) / 2;

  const measures = [
    {
      tag: "Mental-model probe",
      type: "Questionnaire · after each block",
      hyp: "H1, H2",
      body: "Five short slider questions on what the participant believes the aid actually did (e.g., \"how many gauges did it act on?\", \"how often did it skip a gauge that needed attention?\"). Compared against the scenario ground truth — an objective explicability score.",
    },
    {
      tag: "Subjective transparency",
      type: "Questionnaire · after each block",
      hyp: "H1",
      body: "Three ratings: \"the system told me what it was doing\", \"I understood why the system acted or did not act\", \"the amount of information felt about right\". Captures the feeling of being informed — paired with the probe to test the H1 dissociation.",
    },
    {
      tag: "Detection of automation misses",
      type: "Platform log",
      hyp: "H3",
      body: "Whenever the aid skips an event, the participant should catch it manually. We record hit/miss and reaction time.",
    },
    {
      tag: "Non-automated task performance",
      type: "Platform log",
      hyp: "H4",
      body: "Communications: whether each radio call was answered correctly and how quickly. Scheduling: correct entries on a time-table. These tasks the aid does not help with — so they reveal whether reading less in the panel actually frees attention elsewhere.",
    },
  ];

  measures.forEach((m, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.45 + col * (mW + mGap);
    const y = mY + row * (mH + 0.10);
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: mW, h: mH,
      fill: { color: "FFFFFF" }, line: { color: C.panelLine, width: 0.75 },
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.08, h: mH,
      fill: { color: C.navy }, line: { color: C.navy },
    });
    slide.addText(m.tag, {
      x: x + 0.18, y: y + 0.08, w: mW - 1.40, h: 0.30,
      fontFace: FONT, fontSize: 12, bold: true, color: C.navy, margin: 0,
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: x + mW - 1.15, y: y + 0.10, w: 0.95, h: 0.26,
      fill: { color: C.navy }, line: { color: C.navy },
    });
    slide.addText(m.hyp, {
      x: x + mW - 1.15, y: y + 0.11, w: 0.95, h: 0.24,
      fontFace: FONT, fontSize: 10, bold: true, color: "FFFFFF", align: "center", margin: 0,
    });
    slide.addText(m.type, {
      x: x + 0.18, y: y + 0.36, w: mW - 0.30, h: 0.22,
      fontFace: FONT, fontSize: 9, italic: true, color: C.muted, margin: 0,
    });
    slide.addText(m.body, {
      x: x + 0.18, y: y + 0.58, w: mW - 0.30, h: mH - 0.65,
      fontFace: FONT, fontSize: 10.5, color: C.ink, margin: 0, valign: "top",
    });
  });

  const cY = mY + 2 * (mH + 0.10) + 0.05;
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: cY, w: SLIDE_W - 0.9, h: 1.05,
    fill: { color: C.panelBg }, line: { color: C.panelLine, width: 0.75 },
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: cY, w: 0.10, h: 1.05,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  slide.addText("Considerations & limits", {
    x: 0.70, y: cY + 0.06, w: SLIDE_W - 1.15, h: 0.30,
    fontFace: FONT, fontSize: 12, bold: true, color: C.accent, margin: 0,
  });
  slide.addText([
    { text: "Content matching across F1/F2/F3 is the central design constraint — any leak invalidates the form-vs-content comparison.",
      options: { breakLine: true } },
    { text: "Load is held at a single moderate level; generalisation across load levels is a stated limitation, not a confound.",
      options: {} },
  ], {
    x: 0.70, y: cY + 0.36, w: SLIDE_W - 1.15, h: 0.65,
    fontFace: FONT, fontSize: 11, color: C.ink, paraSpaceAfter: 2, margin: 0, valign: "top",
  });
}

pres.writeFile({ fileName: "Form_of_Explanation.pptx" })
    .then((fn) => console.log("Wrote:", fn));
