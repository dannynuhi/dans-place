const fs = require("fs");

const { generateSeeds } = require("../engine/seed");
const { generatePage } = require("../engine/generator");
const { isValid } = require("../engine/qa");
const { layout } = require("../engine/layout");
const { seo } = require("../engine/seo-v2");

fs.mkdirSync("output/pages", { recursive: true });

const seeds = generateSeeds();

let output = [];

for (const seed of seeds) {
  const raw = generatePage(seed);
  const meta = seo(seed);

  const html = layout({
    title: meta.title,
    description: meta.description,
    content: raw
  });

  if (!isValid(html)) continue;

  const file = seed.id + ".html";
  fs.writeFileSync(`output/pages/${file}`, html);

  output.push({ id: seed.id, file });
}

fs.writeFileSync("output/pages.json", JSON.stringify(output, null, 2));

console.log("ORCHESTRATION COMPLETE:", output.length);
