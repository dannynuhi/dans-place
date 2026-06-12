const fs = require("fs");
const { generateSeeds } = require("../engine/seed");
const { generatePage } = require("../engine/generator");
const { isValid } = require("../engine/qa");

const seeds = generateSeeds();

console.log("SEEDS:", seeds.length);

fs.mkdirSync("output/pages", { recursive: true });

let pages = [];

for (const seed of seeds) {
  const page = generatePage(seed);

  console.log("GEN:", seed.id, page.length);

  if (!isValid(page)) {
    console.log("FAIL:", seed.id);
    continue;
  }

  const file = seed.id + ".html";
  fs.writeFileSync(`output/pages/${file}`, page);

  pages.push({ id: seed.id, file });
}

fs.writeFileSync("output/pages.json", JSON.stringify(pages, null, 2));

console.log("DONE:", pages.length);
