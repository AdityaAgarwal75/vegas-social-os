"""Original compatibility patch: managed engine must never launch another browser."""
import sys
from pathlib import Path

p = Path(sys.argv[1]) / 'src/chrome.ts'
s = p.read_text()
old = 'if (!(await cdpUp())) await launchChrome();'
new = '''if (!(await cdpUp())) {
    if (process.env.VSO_FLOW_ATTACH_ONLY === "1") throw new Error("Managed Flow browser is closed. Open its private login browser; no second Chrome was launched.");
    await launchChrome();
  }'''
if s.count(old) != 1:
    raise SystemExit('Pinned browser contract differs; refusing an unverified patch')
p.write_text(s.replace(old, new))

p = Path(sys.argv[1]) / 'src/flow.ts'
s = p.read_text()
old = 'async function applySettings(page: Page, job: Job): Promise<number> {'
if s.count(old) != 1:
    raise SystemExit('Settings contract differs')
s = s.replace(old, 'export async function applySettings(page: Page, job: Job): Promise<number> {')
old = '  if (s.aspect_ratio) await pickRadio(page, s.aspect_ratio);\n  if (s.model) await pickModel(page, s.model);\n  await openSettings(page);'
new = '  if (s.model) await pickModel(page, s.model);\n  await openSettings(page);\n  if (s.aspect_ratio) await pickRadio(page, s.aspect_ratio);'
if s.count(old) != 1:
    raise SystemExit('Model/aspect contract differs')
s = s.replace(old, new)
old = '    await pause(page, 500);\n  }\n}\n\nasync function pickModel'
new = '''    await pause(page, 500);
  }
  if (!(await radio.isChecked())) throw new Error("Requested setting was not retained; nothing generated");
}

async function pickModel'''
if s.count(old) != 1:
    raise SystemExit('Radio verification contract differs')
s = s.replace(old, new)
old = '  await start.click();\n\n  const variants'
new = '''  // Inputs can change the quote: reapply/verify exact controls immediately
  // before the single submission. This does not upload or generate again.
  job.credits = await applySettings(page, job);
  if (job.credits > s.max_credits) throw new Error(`Final Flow quote ${job.credits} exceeds max_credits=${s.max_credits}. Nothing was generated.`);
  await start.click();

  const variants'''
if s.count(old) != 1:
    raise SystemExit('Final credit guard contract differs')
p.write_text(s.replace(old, new))
