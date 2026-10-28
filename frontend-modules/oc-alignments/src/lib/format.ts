// Numbers as the module shows them.

// Costs come in thousandths of an object: a silent model move costs ε = 1.
const UNIT = 1000;

/** A cost as the paper writes it: the deviations, plus ε for every silent move ("3 + 2ε"). */
export const cost = (thousandths: number) => {
  const deviations = Math.floor(thousandths / UNIT);
  const epsilons = thousandths % UNIT;
  if (epsilons === 0) return String(deviations);
  const silent = epsilons === 1 ? "ε" : `${epsilons}ε`;
  return deviations === 0 ? silent : `${deviations} + ${silent}`;
};

export const dateTime = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: "short", timeStyle: "medium" });
