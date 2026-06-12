function generateSeeds() {
  const seeds = [];

  const problems = ["crash","login","error"];
  const software = ["windows","chrome"];
  const contexts = ["usage","update"];
  const versions = ["current"];

  for (let p of problems) {
    for (let s of software) {
      for (let c of contexts) {
        for (let v of versions) {
          seeds.push({
            id: `${p}_${s}_${c}_${v}`,
            p, s, c, v
          });
        }
      }
    }
  }

  return seeds;
}

module.exports = { generateSeeds };
