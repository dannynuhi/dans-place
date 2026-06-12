const problems = [
  "crashes","login","performance","internet","sync",
  "install","update","files","settings","permissions",
  "notifications","errors","device","storage","audio_video"
];

const software = [
  "windows","chrome","android","iphone","excel",
  "word","gmail","drive","discord","notion","canva"
];

const contexts = ["startup","usage","update","account","network"];
const versions = ["current","post_update","legacy"];

function generateSeeds() {
  const seeds = [];
  for (let p of problems) {
    for (let s of software) {
      for (let c of contexts) {
        for (let v of versions) {
          seeds.push({ id: `${p}_${s}_${c}_${v}`, p, s, c, v });
        }
      }
    }
  }
  return seeds;
}

module.exports = { generateSeeds };
