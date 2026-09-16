const pptxgen = require('pptxgenjs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'LIVLINK';
pptx.subject = 'Developer value model';
pptx.title = 'LIVLINK developer value — illustrative 200-unit pilot';
pptx.company = 'LIVLINK';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Cambria',
  bodyFontFace: 'Calibri',
  lang: 'en-US',
};

const slide = pptx.addSlide();
slide.background = { color: 'F7F8FE' };

const navy = '24213F';
const muted = '5C6082';
const lilac = 'EEEBFC';
const violet = '6758CE';
const blue = '496FE8';
const green = '147C54';
const amber = '925800';
const white = 'FFFFFF';
const card = 'FFFFFF';

const shadow = () => ({ type: 'outer', color: '24213F', opacity: 0.10, blur: 2, angle: 45, distance: 1 });

slide.addText('A 200-unit tower gets value before a resident complains', {
  x: 0.65, y: 0.48, w: 9.9, h: 0.45,
  fontFace: 'Cambria', fontSize: 25, bold: true, color: navy, margin: 0,
});
slide.addText('Illustrative pilot model — validate these assumptions with building data before using them as a commercial forecast.', {
  x: 0.67, y: 1.05, w: 11.8, h: 0.28,
  fontFace: 'Calibri', fontSize: 10.5, color: muted, margin: 0,
});

const stats = [
  { x: 0.68, color: violet, number: '12', label: 'device issues detected\nbefore a complaint / month', detail: 'Assumption: 6% of 200 units\nproduce a preventable issue monthly' },
  { x: 4.62, color: blue, number: '6', label: 'diagnostic visits avoided\nper month', detail: 'Assumption: early diagnostics\navoid 50% of initial site visits' },
  { x: 8.56, color: green, number: '4.5 h', label: 'facilities time freed\nper month', detail: 'Assumption: 45 minutes saved\nper avoided diagnosis' },
];

stats.forEach((item) => {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: item.x, y: 1.65, w: 3.45, h: 2.22,
    rectRadius: 0.14, fill: { color: card }, line: { color: 'DFE2F2', width: 1 }, shadow: shadow(),
  });
  slide.addShape(pptx.ShapeType.ellipse, { x: item.x + 0.28, y: 1.96, w: 0.43, h: 0.43, fill: { color: item.color }, line: { color: item.color } });
  slide.addText(item.number, {
    x: item.x + 0.28, y: 2.45, w: 2.75, h: 0.55,
    fontFace: 'Cambria', fontSize: 30, bold: true, color: navy, margin: 0,
  });
  slide.addText(item.label, {
    x: item.x + 0.28, y: 3.03, w: 2.9, h: 0.46,
    fontFace: 'Calibri', fontSize: 12, bold: true, color: navy, breakLine: false, margin: 0,
  });
  slide.addText(item.detail, {
    x: item.x + 0.28, y: 3.50, w: 2.95, h: 0.28,
    fontFace: 'Calibri', fontSize: 8.5, color: muted, margin: 0,
  });
});

slide.addShape(pptx.ShapeType.roundRect, {
  x: 0.68, y: 4.28, w: 11.92, h: 2.28,
  rectRadius: 0.14, fill: { color: lilac }, line: { color: 'D8D2F7', width: 1 },
});
slide.addText('How LIVLINK creates the value', {
  x: 0.98, y: 4.60, w: 3.5, h: 0.30,
  fontFace: 'Cambria', fontSize: 16, bold: true, color: navy, margin: 0,
});

const flow = [
  { x: 0.98, emoji: '1', title: 'Detect', text: 'Simulated telemetry flags\n10% lock battery' },
  { x: 4.17, emoji: '2', title: 'Explain', text: 'Five-reading decline +\nfour connection failures' },
  { x: 7.36, emoji: '3', title: 'Act', text: 'Backend sends a work item\nto the Operator queue' },
  { x: 10.18, emoji: '4', title: 'Prevent', text: 'Assign and fix before\nthe resident reports it' },
];
flow.forEach((item, index) => {
  slide.addShape(pptx.ShapeType.ellipse, { x: item.x, y: 5.15, w: 0.44, h: 0.44, fill: { color: index < 3 ? violet : green }, line: { color: index < 3 ? violet : green } });
  slide.addText(item.emoji, { x: item.x, y: 5.23, w: 0.44, h: 0.14, align: 'center', fontFace: 'Calibri', fontSize: 10, bold: true, color: white, margin: 0 });
  slide.addText(item.title, { x: item.x + 0.56, y: 5.12, w: 1.45, h: 0.21, fontFace: 'Calibri', fontSize: 11, bold: true, color: navy, margin: 0 });
  slide.addText(item.text, { x: item.x + 0.56, y: 5.41, w: 2.25, h: 0.46, fontFace: 'Calibri', fontSize: 8.8, color: muted, margin: 0 });
  if (index < flow.length - 1) {
    slide.addShape(pptx.ShapeType.line, { x: item.x + 2.45, y: 5.37, w: 0.50, h: 0, line: { color: 'A99EE7', width: 1.5, beginArrowType: 'none', endArrowType: 'triangle' } });
  }
});

slide.addText('Use in the pitch: “These are pilot assumptions. LIVLINK gives the developer the measurement layer to replace them with real building data.”', {
  x: 0.69, y: 6.95, w: 11.9, h: 0.24,
  fontFace: 'Calibri', fontSize: 9.5, italic: true, color: amber, margin: 0,
});
slide.addNotes('Talk track: For a 200-unit pilot, we start with transparent assumptions. Twelve preventable issues a month is six percent of homes. If remote diagnostics prevent half of the first site visits, facilities avoid six visits and save 4.5 hours monthly. The important point is that LIVLINK records the real telemetry and work-order outcomes, so this becomes a measured commercial model after a pilot.');

pptx.writeFile({ fileName: 'F:/Projects/CodeFest_Final/docs/LIVLINK_DEVELOPER_VALUE_SLIDE.pptx' });
