function slots(page) {
  return {
    slot1: "after_intro",
    slot2: "mid_fix",
    slot3: "after_solution",
    slot4: page.length > 1200 ? "extra" : null
  };
}
module.exports = { slots };
