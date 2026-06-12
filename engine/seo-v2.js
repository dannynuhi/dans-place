function seo(seed) {
  return {
    title: `${seed.s} ${seed.p} Fix Guide`,
    description: `Step-by-step fix for ${seed.p} issues in ${seed.s} during ${seed.c} usage.`
  };
}

module.exports = { seo };
